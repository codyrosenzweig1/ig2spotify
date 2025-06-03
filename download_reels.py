# download_reels.py

"""
Downloads the first N Reels from a given profile (e.g. "romanianbits") as MP4 files.
Each Reel is saved under downloaded_reels/{profile}/{shortcode}.mp4

Prerequisites:
  1. A `.env` file with:
         IG_USERNAME=your_instagram_username
         IG_PASSWORD=your_instagram_password
  2. instaloader installed:
         pip install instaloader
"""

import os
from dotenv import load_dotenv
import instaloader

# ───────────────────────────────────────────────────────────────────────────────
# 1) Load credentials from .env
# ───────────────────────────────────────────────────────────────────────────────
load_dotenv()
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

if not IG_USERNAME or not IG_PASSWORD:
    raise EnvironmentError("Please set IG_USERNAME and IG_PASSWORD in a .env file")

# Change this to the Instagram handle you want to download Reels from
TARGET_PROFILE = os.getenv("TARGET_USERNAME")
# How many Reels you want to download (e.g., first 10)
MAX_REELS = 10

# ───────────────────────────────────────────────────────────────────────────────
# 2) Configure Instaloader
# ───────────────────────────────────────────────────────────────────────────────
L = instaloader.Instaloader(
    download_videos=True,               # download video files (including Reels)
    download_video_thumbnails=False,    # skip saving the thumbnail images
    save_metadata=False,                # skip JSON metadata files
    dirname_pattern="downloaded_reels/{target}",   # folder: downloaded_reels/romanianbits
    filename_pattern="{shortcode}"      # save each as {shortcode}.mp4
)

# Log in (will use or create a session file in ~/.config/instaloader/)
L.login(IG_USERNAME, IG_PASSWORD)

# ───────────────────────────────────────────────────────────────────────────────
# 3) Fetch the profile and download Reels
# ───────────────────────────────────────────────────────────────────────────────
profile = instaloader.Profile.from_username(L.context, TARGET_PROFILE)
print(f"✔ Logged in. Fetching up to {MAX_REELS} Reels from {TARGET_PROFILE}…")

count = 0
for reel in profile.get_reels():
    if count >= MAX_REELS:
        break

    # Each reel is an Instaloader “Post” object for that Reel
    print(f"→ Downloading Reel #{count + 1}: shortcode = {reel.shortcode}")
    L.download_post(reel, target=profile.username)
    count += 1

print(f"✔ Finished downloading {count} Reel(s).")
