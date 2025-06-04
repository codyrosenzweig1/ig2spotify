import os
import time
import requests
import urllib.parse
from dotenv import load_dotenv

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ───────────────────────────────────────────────────────────────────────────────
# 1) Load Instagram credentials from .env
# ───────────────────────────────────────────────────────────────────────────────
load_dotenv()
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
if not IG_USERNAME or not IG_PASSWORD:
    raise EnvironmentError("Set IG_USERNAME and IG_PASSWORD in a .env file")

TARGET_PROFILE = "romanianbits"   # Change to any handle you want
MAX_TO_FETCH   = 10               # Number of recent Reels to download

# ───────────────────────────────────────────────────────────────────────────────
# 2) Configure Selenium-Wire WebDriver (Chrome)
# ───────────────────────────────────────────────────────────────────────────────
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1200,900")

driver = webdriver.Chrome(options=chrome_options)
wait   = WebDriverWait(driver, 15)

# ───────────────────────────────────────────────────────────────────────────────
# 3) Utility Functions
# ───────────────────────────────────────────────────────────────────────────────

def clean_mp4_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    qs.pop("bytestart", None)
    qs.pop("byteend",   None)
    new_query = urllib.parse.urlencode(qs, doseq=True)
    cleaned = parsed._replace(query=new_query)
    return urllib.parse.urlunparse(cleaned)


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
            not_now = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and normalize-space(text())='Not now']"))
            )
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

    anchors = driver.find_elements(
        By.XPATH,
        f"//a[contains(@href, '/{TARGET_PROFILE}/reel/')]"
    )

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


def fetch_all_mp4_urls(shortcode: str):
    driver.requests.clear()
    reel_url = f"https://www.instagram.com/reel/{shortcode}/"
    driver.get(reel_url)

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    except:
        print(f"   ✖ Timeout waiting for <video> on {reel_url}")
        return []

    time.sleep(3)

    urls = []
    seen = set()

    for req in driver.requests:
        if not req.response:
            continue
        if req.path.lower().endswith(".mp4"):
            cleaned = clean_mp4_url(req.url)
            if cleaned not in seen:
                seen.add(cleaned)
                urls.append(cleaned)

    if not urls:
        print(f"   ✖ No .mp4 files found for {shortcode}")
    else:
        print(f"   → Found {len(urls)} MP4s for {shortcode}")
        for u in urls:
            print(f"      ↳ {u}")

    return urls


def download_file(url: str, dest_path: str):
    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"], domain=c["domain"])

    print(f"   → Downloading: {url}")
    try:
        resp = session.get(url, stream=True, timeout=30)
        print(f"      ← HTTP {resp.status_code}, Content-Type: {resp.headers.get('Content-Type')}")
        resp.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"   ✔ Saved to {dest_path}")

    except Exception as e:
        print(f"   ✖ Error downloading {url}: {e}")


# ───────────────────────────────────────────────────────────────────────────────
# 4) Main Logic
# ───────────────────────────────────────────────────────────────────────────────

def main():
    insta_login()

    codes = collect_reel_shortcodes()
    if not codes:
        print("No Reels found; exiting.")
        driver.quit()
        return

    out_dir = os.path.join("downloaded_reels", TARGET_PROFILE)
    os.makedirs(out_dir, exist_ok=True)

    for idx, code in enumerate(codes, 1):
        print(f"\n[{idx}/{len(codes)}] Processing Reel {code}")
        mp4_urls = fetch_all_mp4_urls(code)
        if mp4_urls:
            for i, url in enumerate(mp4_urls, 1):
                dest_file = os.path.join(out_dir, f"{code}_{i}.mp4")
                if os.path.isfile(dest_file):
                    print(f"   → {dest_file} already exists; skipping.")
                else:
                    download_file(url, dest_file)
        else:
            print(f"   → Skipping {code} (no MP4 files found)")

        time.sleep(2)

    print("\n✔ All done. Check the folder:", out_dir)
    driver.quit()


if __name__ == "__main__":
    main()
