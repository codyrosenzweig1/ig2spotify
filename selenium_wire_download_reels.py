import os
import time
import requests
import urllib.parse
import base64
import json
from datetime import datetime
from dotenv import load_dotenv

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load Instagram credentials from .env file
load_dotenv()
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
if not IG_USERNAME or not IG_PASSWORD:
    raise EnvironmentError("Set IG_USERNAME and IG_PASSWORD in a .env file")

TARGET_PROFILE = "romanianbits"
MAX_REELS = 4  # Limit how many reels to process

# Setup Chrome with visible window
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1200,900")

# Launch browser with Selenium Wire to capture network traffic
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

# Clean URL by removing byte range parameters for comparison
def clean_mp4_url(url):
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    qs.pop("bytestart", None)
    qs.pop("byteend", None)
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

# Extract and decode 'efg' query parameter to access metadata
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

# Login to Instagram and give time to manually handle MFA popups
def insta_login():
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    wait.until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(IG_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(IG_PASSWORD + Keys.ENTER)
    try:
        not_now = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and normalize-space(text())='Not now']")))
        not_now.click()
    except:
        pass
    # time.sleep(2)  # Allow time for MFA or other popups
    print("✔ Logged in successfully.")

# Parse requests to find audio segment packets based on vencode_tag
def find_audio_stream_packets(all_requests):
    audio_streams = {}
    for req in all_requests:
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

    # Print out all streams for debugging
    for base, segments in audio_streams.items():
        segments.sort()
        print(f"\nAudio stream base: {base}")
        for s in segments:
            print(f"  bytestart={s[0]} → byteend={s[1]}")
    return audio_streams

# Download audio segments sequentially and write to file
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

# Open the first reel on the target profile
def open_first_reel():
    driver.get(f"https://www.instagram.com/{TARGET_PROFILE}/reels/")
    time.sleep(3)
    first_reel = wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '/{TARGET_PROFILE}/reel/')]")))
    first_reel.click()
    print("✔ Opened first reel.")

# Let network traffic collect after video starts playing
def watch_and_capture_packets():
    print("⏳ Waiting for video element to appear...")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    print("▶️ Video found, sleeping to let network packets accumulate...")
    time.sleep(10)

# Simulate arrow key to move to next reel
def go_to_next_reel():
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ARROW_RIGHT)
        print("→ Sent ARROW_RIGHT to move to next reel.")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"✖ Failed to move to next reel: {e}")
        return False

# Main automation loop
def download_user_reels(target_profile):
    insta_login()
    open_first_reel()
    out_dir = os.path.join("downloaded_reels", target_profile)
    os.makedirs(out_dir, exist_ok=True)
    reel_counter = 0
    seen_audio_bases = set()
    all_requests = []

    while True:
        if reel_counter >= MAX_REELS:
            print(f"✅ Reached max of {MAX_REELS} reels. Exiting.")
            break

        driver.requests.clear()
        watch_and_capture_packets()
        all_requests.extend(driver.requests)

        audio_packets = find_audio_stream_packets(all_requests)

        # Filter: Only streams that begin at byte 0 (likely full audio)
        valid_streams = [(base, segs) for base, segs in audio_packets.items() if any(s[0] == 0 for s in segs)]
        if not valid_streams:
            print("✖ No valid stream with bytestart=0 found.")
            continue

        # Select the last matching stream as most recent
        best_stream_base, best_segments = valid_streams[-1]

        if best_stream_base in seen_audio_bases:
            print("⚠ Skipping duplicate audio stream. Already processed:")
            print(f"   Base: {best_stream_base}")
            for start, end, _ in best_segments:
                print(f"     - {start} to {end}")
        else:
            print("✔ Selected new audio stream:")
            print(f"   Base: {best_stream_base}")
            for start, end, _ in best_segments:
                print(f"     - {start} to {end}")

            seen_audio_bases.add(best_stream_base)
            best_segments.sort()
            dest_file = os.path.join(out_dir, f"{TARGET_PROFILE}_reel_{reel_counter}_audio.mp4") # change mp4 to mp3 to download straight away as mp3
            download_audio_segments(best_stream_base, best_segments, dest_file)
            reel_counter += 1

            # Cleanup: remove requests related to the used audio stream to avoid duplicates and free memory
            all_requests = [r for r in all_requests if best_stream_base not in r.url]

        if not go_to_next_reel():
            break

    driver.quit()

# if __name__ == "__main__":
#     main()
