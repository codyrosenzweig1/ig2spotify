# selenium_wire_download_reels.py

"""
Downloads Instagram Reels by capturing the real CDN URL via Selenium-Wire.

Workflow:
  1) Log in to Instagram via Selenium (so we obtain valid auth cookies).
  2) Go to /<profile>/reels/ and collect up to MAX_TO_FETCH shortcodes.
  3) For each shortcode:
       a) Clear the browser’s request log.
       b) Visit https://www.instagram.com/reel/<SHORTCODE>/.
       c) Wait until the <video> element appears and starts loading.
       d) Inspect Selenium-Wire’s captured requests; pick out the one whose URL ends with ".mp4".
       e) Use requests (with the same cookies) to download that URL to disk.
"""

import os
import time
import requests
from dotenv import load_dotenv

# Use seleniumwire instead of selenium
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

TARGET_PROFILE = "romanianbits"   # Change to the handle you want
MAX_TO_FETCH   = 10               # Number of recent Reels to download

# ───────────────────────────────────────────────────────────────────────────────
# 2) Configure Selenium-Wire WebDriver (Chrome)
# ───────────────────────────────────────────────────────────────────────────────
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment for headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1200,900")

# Selenium-Wire lets us inspect network requests
driver = webdriver.Chrome(options=chrome_options)
wait   = WebDriverWait(driver, 15)

def insta_login():
    """
    Logs in to Instagram via Selenium, dismisses the ‘Save Login Info?’ popup if it appears.
    """
    driver.get("https://www.instagram.com/accounts/login/")
    wait.until(EC.presence_of_element_located((By.NAME, "username")))

    driver.find_element(By.NAME, "username").send_keys(IG_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(IG_PASSWORD + Keys.ENTER)

    # Wait either for the search box (successful login) or the “Save Login Info?” dialog
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']")))
    except:
        # Dismiss “Save Your Login Info?” if shown
        try:
            not_now = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Not Now']"))
            )
            not_now.click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']")))
        except:
            pass

    print("✔ Logged in successfully.")

def collect_reel_shortcodes():
    """
    Goes to /<profile>/reels/ and returns a list of up to MAX_TO_FETCH shortcodes.
    """
    reels_page = f"https://www.instagram.com/{TARGET_PROFILE}/reels/"
    driver.get(reels_page)
    time.sleep(3)  # Let thumbnails load

    # Scroll to force lazy‐load
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

def fetch_cdn_mp4_url(shortcode):
    """
    Visits https://www.instagram.com/reel/<shortcode>/ and captures the network
    request that fetches the actual .mp4. Returns that URL (including any signed tokens).
    """
    # Clear any previously captured requests
    driver.requests.clear()

    reel_url = f"https://www.instagram.com/reel/{shortcode}/"
    driver.get(reel_url)

    # Wait until the <video> element is present
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
    except:
        print(f"   ✖ Timeout waiting for video element on {reel_url}")
        return None

    # Give it a second to let the video request fire
    time.sleep(2)

    # Inspect captured requests for a URL that ends with ".mp4"
    for request in driver.requests:
        if request.response and request.path.endswith(".mp4"):
            mp4_url = request.url
            print(f"   → Captured CDN MP4 URL for {shortcode}: {mp4_url}")
            return mp4_url

    print(f"   ✖ Could not find .mp4 request for {shortcode}")
    return None

def download_file(url, dest_path):
    """
    Downloads a file from 'url' to 'dest_path' using requests,
    and prints status code / content-type for debugging.
    """
    # Transfer cookies from Selenium into this session
    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"], domain=c["domain"])

    print(f"   → Attempting to download: {url}")
    try:
        # Use stream=True so we can inspect headers before writing
        resp = session.get(url, stream=True, timeout=30)
        print(f"      ← HTTP {resp.status_code}, Content-Type: {resp.headers.get('Content-Type')}")
        resp.raise_for_status()

        # If it really is an MP4, Content-Type should be “video/mp4” (or similar).
        # If it’s text/html or a redirect, we know why the file is tiny.

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"   ✔ Saved to {dest_path}")

    except Exception as e:
        print(f"   ✖ Error downloading {url}: {e}")


def main():
    # 1) Log in
    insta_login()

    # 2) Grab Reel shortcodes
    codes = collect_reel_shortcodes()
    if not codes:
        print("No Reels found; exiting.")
        driver.quit()
        return

    # 3) Ensure output directory exists
    out_dir = os.path.join("downloaded_reels", TARGET_PROFILE)
    os.makedirs(out_dir, exist_ok=True)

    # 4) For each shortcode: capture the real MP4 URL and download
    for idx, code in enumerate(codes, 1):
        print(f"\n[{idx}/{len(codes)}] Processing Reel {code}")
        mp4_url = fetch_cdn_mp4_url(code)
        if mp4_url:
            dest_file = os.path.join(out_dir, f"{code}.mp4")
            if os.path.isfile(dest_file):
                print(f"   → {dest_file} already exists; skipping.")
            else:
                download_file(mp4_url, dest_file)
        else:
            print(f"   → Skipping {code} (could not find CDN URL)")

        # Small pause to avoid tripping any further rate limits
        time.sleep(2)

    print("\n✔ All done. Check the folder:", out_dir)
    driver.quit()

if __name__ == "__main__":
    main()
