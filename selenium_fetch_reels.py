# selenium_fetch_reels_handle_save.py

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load environment variables from .env
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
IG_USERNAME    = os.getenv("IG_USERNAME")
IG_PASSWORD    = os.getenv("IG_PASSWORD")
TARGET_PROFILE = os.getenv("TARGET_USERNAME")

if not IG_USERNAME or not IG_PASSWORD or not TARGET_PROFILE:
    raise EnvironmentError("Ensure IG_USERNAME, IG_PASSWORD, and TARGET_USERNAME are set in .env")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Configure Selenium ChromeOptions (visible window for debugging)
# ─────────────────────────────────────────────────────────────────────────────
chrome_options = Options()
# chrome_options.add_argument("--headless")           # Uncomment this line to run headless
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1400,1000")

# If ChromeDriver is not on your PATH, specify executable_path here:
# driver = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver", options=chrome_options)
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)  # up to 15 seconds for explicit waits

try:
    # ─────────────────────────────────────────────────────────────────────────
    # 3. Navigate to Instagram login page & log in
    # ─────────────────────────────────────────────────────────────────────────
    print("→ Opening Instagram login page…")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)  # allow login form to appear

    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    username_input.send_keys(IG_USERNAME)
    password_input.send_keys(IG_PASSWORD)
    password_input.submit()

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Handle “Save Your Login Info?” prompt and wait for home feed
    # ─────────────────────────────────────────────────────────────────────────
    print("→ Submitted credentials, waiting for post-login page…")
    try:
        # Wait for either the “Save Your Login Info?” modal OR the Search box on home page
        # The “Not Now” button on the modal has text “Not Now”
        not_now_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']"))
        )
        # If this appears first, click “Not Now”
        not_now_button.click()
        print("   → Clicked 'Not Now' on Save Your Login Info prompt.")
        time.sleep(2)
    except TimeoutException:
        # If “Not Now” did not appear, perhaps Instagram skipped directly to home feed
        print("   → 'Save Your Login Info?' did not appear (or timed out).")

    # Now wait for the Search box to confirm we’re logged in
    # 1. Capture the URL before submitting
    before = driver.current_url  # should be "https://www.instagram.com/accounts/login/"

    # 2. Submit and then wait until the URL changes (or a timeout)
    password_input.submit()

    # 3. Poll for up to, say, 10 seconds, until driver.current_url != before
    for _ in range(20):
        if driver.current_url != before:
            break
        time.sleep(0.5)

    # 4. Check whether it actually changed
    if driver.current_url == before:
        print("[ERROR] URL never changed after login—likely login failed or a challenge appeared.")
        driver.save_screenshot("login_error.png")
        driver.quit()
        exit(1)

    print("✅ Login seems to have succeeded (URL changed). Current URL:", driver.current_url)


    # # Optionally handle any “Turn on Notifications” prompt similarly:
    # try:
    #     not_now_notifications = driver.find_element(By.XPATH, "//button[text()='Not Now']")
    #     not_now_notifications.click()
    #     print("   → Clicked 'Not Now' on Turn on Notifications prompt.")
    #     time.sleep(2)
    # except NoSuchElementException:
    #     pass  # no notifications prompt

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Navigate directly to the Reels grid page for the target profile
    # ─────────────────────────────────────────────────────────────────────────
    reels_url = f"https://www.instagram.com/{TARGET_PROFILE}/reels/"
    print(f"→ Navigating to {reels_url}")
    driver.get(reels_url)
    time.sleep(5)  # allow the Reels grid to render

    print("[DEBUG] Current URL after navigating to Reels:", driver.current_url)
    print("[DEBUG] Page title:", driver.title)

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Scroll down several times to load more Reel thumbnails
    # ─────────────────────────────────────────────────────────────────────────
    for i in range(4):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        print(f"[DEBUG] After scroll #{i+1}, page_source length: {len(driver.page_source)}")

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Locate thumbnail <div role='button'> elements that wrap Reel thumbnails
    # ─────────────────────────────────────────────────────────────────────────
    thumbnails = driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
    print(f"[DEBUG] Found {len(thumbnails)} elements with role='button' on Reels page.")

    # Filter only those <div role='button'> that contain an <a> with '/reel/' in href
    candidate_thumbnails = []
    for thumb in thumbnails:
        try:
            # Within this <div>, find a nested <a> whose href contains '/reel/'
            thumb.find_element(By.XPATH, ".//a[contains(@href, '/reel/')]")
            candidate_thumbnails.append(thumb)
        except NoSuchElementException:
            continue
        if len(candidate_thumbnails) >= 5:
            break

    print(f"[DEBUG] Identified {len(candidate_thumbnails)} candidate thumbnail(s) to click for reels.")

    # ─────────────────────────────────────────────────────────────────────────
    # 8. Click each candidate thumbnail to open the Reel modal & extract <video> src
    # ─────────────────────────────────────────────────────────────────────────
    reel_mp4_urls = []
    for idx, thumb in enumerate(candidate_thumbnails, start=1):
        try:
            # Scroll the thumbnail into view, then click it
            driver.execute_script("arguments[0].scrollIntoView(true);", thumb)
            time.sleep(1)
            thumb.click()
        except ElementClickInterceptedException:
            print(f"[WARN] Could not click thumbnail #{idx}. Skipping.")
            continue

        # Wait for the <video> element to appear in the overlay
        try:
            video_elem = wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            mp4_url = video_elem.get_attribute("src")
            print(f"[TEST] Reel #{idx} MP4 URL: {mp4_url}")
            reel_mp4_urls.append(mp4_url)
        except TimeoutException:
            print(f"[WARN] After clicking thumbnail #{idx}, no <video> appeared. Skipping this one.")

        # Close the modal by sending ESCAPE to the body
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(2)
        except Exception:
            pass  # if ESC didn’t close it, it will close on next iteration

    if not reel_mp4_urls:
        print("[ERROR] No MP4 URLs extracted. Check if the thumbnails were correct and videos loaded.")
    else:
        print("[TEST] Successfully extracted MP4 URLs from the selected reels:")
        for i, url in enumerate(reel_mp4_urls, start=1):
            print(f"  {i}. {url}")

    # ─────────────────────────────────────────────────────────────────────────
    # 9. (Optional) Save these MP4 URLs somewhere or proceed to FFmpeg + Shazamio
    # ─────────────────────────────────────────────────────────────────────────
    # For now, we simply printed them above. Next, feed each url into your audio extractor.

finally:
    # ─────────────────────────────────────────────────────────────────────────
    # 10. Clean up—close the browser
    # ─────────────────────────────────────────────────────────────────────────
    print("→ Closing browser.")
    driver.quit()
