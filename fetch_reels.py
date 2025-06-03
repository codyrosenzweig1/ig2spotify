# selenium_fetch_reels_arrow.py

"""
Logs into Instagram, opens the first Reel for a given profile (e.g. “romanianbits”),
then repeatedly sends the RIGHT→ARROW key to advance through all preloaded Reels.
Collects each <video> src (“blob:…” URL) in a list for later processing.
"""

import os
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ───────────────────────────────────────────────────────────────────────────────
# 1) Load Instagram credentials from .env
# ───────────────────────────────────────────────────────────────────────────────
load_dotenv()
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

if not IG_USERNAME or not IG_PASSWORD:
    raise EnvironmentError("Please set IG_USERNAME and IG_PASSWORD in a .env file")

# Change this to the Instagram handle you want to scrape
TARGET_PROFILE = "romanianbits"

# ───────────────────────────────────────────────────────────────────────────────
# 2) Configure Selenium’s Chrome WebDriver
# ───────────────────────────────────────────────────────────────────────────────
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment if you want no GUI
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1400,1000")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

try:
    # ───────────────────────────────────────────────────────────────────────────
    # 3) Log in to Instagram
    # ───────────────────────────────────────────────────────────────────────────
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(2)  # allow form to appear

    user_input = driver.find_element(By.NAME, "username")
    pass_input = driver.find_element(By.NAME, "password")
    user_input.send_keys(IG_USERNAME)
    pass_input.send_keys(IG_PASSWORD)
    pass_input.submit()

    # ───────────────────────────────────────────────────────────────────────────
    # 4) Dismiss “Save Your Login Info?” if it appears
    # ───────────────────────────────────────────────────────────────────────────
    try:
        not_now = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@role='button' and normalize-space(text())='Not now']")
            )
        )
        not_now.click()
        print("✔ Dismissed ‘Save Your Login Info?’ prompt")
        time.sleep(1)
    except TimeoutException:
        # Popup did not appear—just continue
        print("ℹ ‘Not now’ popup did not appear; continuing")

    # ───────────────────────────────────────────────────────────────────────────
    # 5) Go directly to the user’s Reels grid
    # ───────────────────────────────────────────────────────────────────────────
    reels_url = f"https://www.instagram.com/{TARGET_PROFILE}/reels/"
    driver.get(reels_url)
    time.sleep(3)  # allow thumbnails to load
    print(f"✔ Opened {reels_url}")

    # ───────────────────────────────────────────────────────────────────────────
    # 6) Click the first Reel thumbnail (div._aajy)
    # ───────────────────────────────────────────────────────────────────────────
    try:
        # Wait until at least one Reel thumbnail <a> appears, then click it:
        first_reel = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/reel/')][1]"))
        )
        first_reel.click()
        print("✔ Opened first Reel overlay")
        time.sleep(2)  # wait for video overlay to render
        
    except TimeoutException:
        print("[ERROR] No Reel thumbnail found. Exiting.")
        driver.quit()
        exit(1)

    # ───────────────────────────────────────────────────────────────────────────
    # 7) Loop: grab each <video> URL, then send RIGHT→ARROW to advance
    # ───────────────────────────────────────────────────────────────────────────
    collected_mp4_urls = []

    while True:
        # (A) Wait for the <video> element in the overlay to appear
        try:
            video_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            blob_url = video_element.get_attribute("src")
            print("🎬 Collected MP4 URL:", blob_url)
            collected_mp4_urls.append(blob_url)
        except TimeoutException:
            print("[WARN] No <video> found; overlay may have closed. Stopping.")
            break

        # (B) Advance using the RIGHT ARROW key
        # Sending ARROW_RIGHT should move from the current Reel to the next one
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_RIGHT)
            time.sleep(1.5)  # wait for the next video to load
        except Exception as e:
            print("ℹ Could not send ARROW_RIGHT (maybe end of Reels). Stopping.")
            break

        # (C) Loop continues, grabbing the new <video> URL
        # If Instagram didn’t preload a next Reel, a subsequent wait→video will time out

    # ───────────────────────────────────────────────────────────────────────────
    # 8) Close the overlay (send ESC)
    # ───────────────────────────────────────────────────────────────────────────
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        print("✔ Closed Reel overlay")
        time.sleep(0.5)
    except:
        pass

    # ───────────────────────────────────────────────────────────────────────────
    # 9) Print all collected blob: URLs
    # ───────────────────────────────────────────────────────────────────────────
    if collected_mp4_urls:
        print("\n[RESULT] All collected MP4 URLs:")
        for i, url in enumerate(collected_mp4_urls, start=1):
            print(f"  {i}. {url}")
    else:
        print("\n[RESULT] No videos were collected.")

finally:
    print("→ Closing browser.")
    driver.quit()
