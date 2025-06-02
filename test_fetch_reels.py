# selenium_fetch_reels.py

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load environment variables from .env
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
IG_USERNAME    = os.getenv("IG_USERNAME")
IG_PASSWORD    = os.getenv("IG_PASSWORD")
TARGET_PROFILE = os.getenv("TARGET_USERNAME")

if not IG_USERNAME or not IG_PASSWORD or not TARGET_PROFILE:
    raise EnvironmentError(
        "Ensure IG_USERNAME, IG_PASSWORD, and TARGET_USERNAME are set in .env"
    )

# ─────────────────────────────────────────────────────────────────────────────
# 2. Configure Selenium: headless Chrome with a large viewport
# ─────────────────────────────────────────────────────────────────────────────
chrome_options = Options()
chrome_options.add_argument("--headless")             # run without a visible window
chrome_options.add_argument("--disable-gpu")          # recommended for headless on some OSes
chrome_options.add_argument("--window-size=1200,800") # ensures Reels grid loads in desktop layout

driver = webdriver.Chrome(options=chrome_options)

try:
    # ─────────────────────────────────────────────────────────────────────────
    # 3. Navigate to Instagram login page & log in
    # ─────────────────────────────────────────────────────────────────────────
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)  # wait for login form to appear (inputs & buttons)

    # Locate username/password fields and submit credentials
    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    username_input.send_keys(IG_USERNAME)
    password_input.send_keys(IG_PASSWORD)
    password_input.submit()

    # Wait for Instagram’s home feed or user’s profile to load after login
    time.sleep(5)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Navigate directly to the Reels page for the target profile
    # ─────────────────────────────────────────────────────────────────────────
    reels_url = f"https://www.instagram.com/{TARGET_PROFILE}/reels/"
    driver.get(reels_url)
    time.sleep(5)  # wait for Reels grid to load

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Scroll down within the Reels grid to load thumbnails
    # ─────────────────────────────────────────────────────────────────────────
    # Instagram loads only a handful of Reels at first; scrolling forces more to appear
    for _ in range(3):               
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Find Reel page links from the Reels grid
    # ─────────────────────────────────────────────────────────────────────────
    # Each thumbnail is typically wrapped in an <a> with '/reel/SHORTCODE/'
    reels = driver.find_elements(By.XPATH, "//a[contains(@href, '/reel/')]")
    seen = set()
    reel_urls = []
    for reel in reels:
        href = reel.get_attribute("href")
        if href and href not in seen:
            seen.add(href)
            reel_urls.append(href)
        if len(reel_urls) >= 5:  # limit to first 5 for testing
            break

    if not reel_urls:
        print("[ERROR] No Reel URLs found on the Reels page. The account may have no public Reels.")
    else:
        print("[TEST] Found Reel page URLs:")
        for idx, r in enumerate(reel_urls, start=1):
            print(f"  {idx}. {r}")

    # ─────────────────────────────────────────────────────────────────────────
    # 7. (Optional) Get the direct MP4 URL for each Reel:
    #    - Visit each Reel page URL
    #    - Find the <video> tag and read its 'src' attribute
    # ─────────────────────────────────────────────────────────────────────────
    #
    # Uncomment if you want to immediately extract the MP4 URLs:
    #
    # for r in reel_urls:
    #     driver.get(r)
    #     time.sleep(3)  # wait for the video element to load
    #     try:
    #         video = driver.find_element(By.TAG_NAME, "video")
    #         mp4_url = video.get_attribute("src")
    #         print(f"    → MP4 URL: {mp4_url}")
    #     except NoSuchElementException:
    #         print(f"    [WARN] No <video> tag found on {r}")
    #

finally:
    # ─────────────────────────────────────────────────────────────────────────
    # 8. Clean up—close the browser
    # ─────────────────────────────────────────────────────────────────────────
    driver.quit()
