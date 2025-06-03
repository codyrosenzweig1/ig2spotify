# selenium_fetch_reels_romanianbits.py

import time
import os
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load Instagram credentials and target profile from .env
# ─────────────────────────────────────────────────────────────────────────────
# Ensure you have a .env file in the same directory with:
#   IG_USERNAME=your_instagram_username
#   IG_PASSWORD=your_instagram_password
load_dotenv()
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

if not IG_USERNAME or not IG_PASSWORD:
    raise EnvironmentError("Please set IG_USERNAME and IG_PASSWORD in your .env file")

# The profile whose Reels we want—here, “romanianbits”
TARGET_PROFILE = "romanianbits"

# ─────────────────────────────────────────────────────────────────────────────
# 2. Configure Selenium to launch Chrome (visible window for debugging)
# ─────────────────────────────────────────────────────────────────────────────
chrome_options = Options()
# To run without opening a visible window, uncomment the following line:
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1400,1000")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)  # for explicit waits up to 15 seconds

try:
    # ─────────────────────────────────────────────────────────────────────────
    # 3. Navigate to Instagram’s login page & submit credentials
    # ─────────────────────────────────────────────────────────────────────────
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(2)  # allow the login form to render

    # Locate the username/password input fields
    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")

    # Enter credentials
    username_input.send_keys(IG_USERNAME)
    password_input.send_keys(IG_PASSWORD)
    password_input.submit()  # submit the form

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Handle the “Save Your Login Info?” popup by clicking “Not Now”
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # Wait until a <div role="button"> with text “Not now” appears and click it
        not_now_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@role='button' and normalize-space(text())='Not now']")
            )
        )
        not_now_button.click()
        print("→ Clicked ‘Not now’ on Save-Login-Info popup.")
        time.sleep(1)
    except TimeoutException:
        # If the popup never appears within 15s, skip silently
        print("→ ‘Not now’ popup did not appear—continuing.")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Now that we’re logged in, navigate directly to romanianbits’ Reels page
    # ─────────────────────────────────────────────────────────────────────────
    reels_url = f"https://www.instagram.com/{TARGET_PROFILE}/reels/"
    driver.get(reels_url)
    time.sleep(5)  # allow the Reels grid to render

    print(f"→ Navigated to {reels_url}")
    print("[DEBUG] Current page title:", driver.title)

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Scroll the Reels grid a few times so that multiple thumbnails load
    # ─────────────────────────────────────────────────────────────────────────
    try:
        first_thumb = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div._aajy"))
        )
        # Scroll it into view (in case it’s slightly off-screen)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_thumb)
        time.sleep(0.5)
        first_thumb.click()
        print("→ Opened first Reel overlay")
    except TimeoutException:
        print("[ERROR] Could not find a div._aaj y. The page may not have loaded any thumbnails yet.")
        driver.quit()
        exit(1)
    # ─────────────────────────────────────────────────────────────────────────
    # 7. Locate all <div class="_aajy"> elements—each is a Reel thumbnail container
    # ─────────────────────────────────────────────────────────────────────────
    reel_mp4_urls = []
    while True:
        # 7A. Wait for the <video> element in the overlay
        try:
            video_elem = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            mp4_url = video_elem.get_attribute("src")
            print("🎬 Collected MP4 URL:", mp4_url)
            reel_mp4_urls.append(mp4_url)
        except TimeoutException:
            print("[WARN] No <video> found in the overlay. Exiting loop.")
            break

        try:
            time.sleep(1)  # give time for the next button to load
            next_button = driver.find_element(By.XPATH, "//button[.//svg[@aria-label='Next']]")
            # Scroll it into view and click
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(0.3)
            next_button.click()
            print("→ Clicked Next to advance to the next Reel")
            time.sleep(1.5)  # let the next video load
        except NoSuchElementException:
            print("→ No Next button found—reached end of preloaded Reels.")
            break
        except ElementClickInterceptedException:
            print("[WARN] Next button was not clickable. Retrying after a brief pause…")
            time.sleep(1)
            continue



    #  ─────────────────────────────────────────────────────────────────────────
    # 8. Close the overlay via ESC
    # ─────────────────────────────────────────────────────────────────────────
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        time.sleep(1)
        print("→ Closed the Reel overlay")
    except NoSuchElementException:
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # 9. Print all collected MP4 URLs
    # ─────────────────────────────────────────────────────────────────────────
    if reel_mp4_urls:
        print("[RESULT] Collected the following MP4 URLs:")
        for i, url in enumerate(reel_mp4_urls, start=1):
            print(f"  {i}. {url}")
    else:
        print("[RESULT] No MP4 URLs were collected.")

finally:
    # ─────────────────────────────────────────────────────────────────────────
    # 10. Clean up—close the browser
    # ─────────────────────────────────────────────────────────────────────────
    print("→ Closing browser.")
    driver.quit()
