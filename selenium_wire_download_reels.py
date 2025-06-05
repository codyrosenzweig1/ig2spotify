import os
import time
import requests
import urllib.parse
import base64
import json
from dotenv import load_dotenv

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
if not IG_USERNAME or not IG_PASSWORD:
    raise EnvironmentError("Set IG_USERNAME and IG_PASSWORD in a .env file")

TARGET_PROFILE = "romanianbits"
MAX_TO_FETCH = 3

chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1200,900")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

def clean_mp4_url(url):
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    qs.pop("bytestart", None)
    qs.pop("byteend", None)
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

def extract_efg(url):
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    efg_val = qs.get("efg", [None])[0]
    if efg_val:
        try:
            decoded = base64.b64decode(efg_val + "==").decode("utf-8")
            return json.loads(decoded)
        except Exception:
            return {}
    return {}

def insta_login():
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    wait.until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(IG_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(IG_PASSWORD + Keys.ENTER)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']")))
    except:
        try:
            not_now = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and normalize-space(text())='Not now']")))
            not_now.click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']")))
        except:
            pass
    print("✔ Logged in successfully.")

def collect_reel_shortcodes():
    time.sleep(5)
    reels_page = f"https://www.instagram.com/{TARGET_PROFILE}/reels/"
    driver.get(reels_page)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    anchors = driver.find_elements(By.XPATH, f"//a[contains(@href, '/{TARGET_PROFILE}/reel/')]")
    shortcodes = []
    seen = set()
    for a in anchors:
        href = a.get_attribute("href").strip("/")
        parts = href.split("/")
        if len(parts) >= 2 and parts[-2] == "reel":
            code = parts[-1]
            if code not in seen:
                seen.add(code)
                shortcodes.append(code)
            if len(shortcodes) >= MAX_TO_FETCH:
                break
    print(f"✔ Collected {len(shortcodes)} Reel shortcodes: {shortcodes}")
    return shortcodes

def find_audio_stream_packets():
    audio_streams = {}
    for req in driver.requests:
        if not req.response or not req.path.lower().endswith(".mp4"):
            continue
        efg = extract_efg(req.url)
        tag = efg.get("vencode_tag", "")
        if "heaac" in tag and "audio" in tag:
            parsed = urllib.parse.urlparse(req.url)
            base = parsed.scheme + "://" + parsed.netloc + parsed.path
            qs = urllib.parse.parse_qs(parsed.query)
            start = int(qs.get("bytestart", ["0"])[0])
            end = int(qs.get("byteend", ["0"])[0])
            audio_streams.setdefault(base, []).append((start, end, req.url))
    for base, segments in audio_streams.items():
        segments.sort()
        print(f"\nAudio stream base: {base}")
        for s in segments:
            print(f"  bytestart={s[0]} → byteend={s[1]}")
    return audio_streams

def download_audio_segments(stream_base, segments, dest_path):
    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"], domain=c["domain"])
    with open(dest_path, "wb") as f:
        for start, end, url in segments:
            print(f"   → Downloading bytes {start}-{end}")
            try:
                resp = session.get(url, stream=True, timeout=30)
                resp.raise_for_status()
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            except Exception as e:
                print(f"   ✖ Failed to download segment {start}-{end}: {e}")
    print(f"   ✔ Audio saved to {dest_path}")

def main():
    insta_login()
    codes = collect_reel_shortcodes()
    if not codes:
        print("No Reels found; exiting.")
        driver.quit()
        return

    shortcode = codes[0]
    print(f"\n→ Visiting reel: {shortcode}")
    driver.requests.clear()
    driver.get(f"https://www.instagram.com/reel/{shortcode}/")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    time.sleep(4)
    audio_packets = find_audio_stream_packets()
    if not audio_packets:
        print("✖ No audio stream packets found.")
    else:
        out_dir = os.path.join("downloaded_reels", TARGET_PROFILE)
        os.makedirs(out_dir, exist_ok=True)
        audio_stream_base = list(audio_packets.keys())[0]
        audio_segments = audio_packets[audio_stream_base]
        audio_segments.sort()
        dest_file = os.path.join(out_dir, f"{shortcode}_audio.mp4")
        download_audio_segments(audio_stream_base, audio_segments, dest_file)

    driver.quit()

if __name__ == "__main__":
    main()
