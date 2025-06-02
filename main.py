# Standard library imports
import os            # for environment variables and path manipulation
import asyncio       # for asynchronous concurrency
import subprocess    # to call FFmpeg as a subprocess

# Third-party imports
import instaloader    # to fetch Instagram Reels metadata without manual scraping
from shazamio import Shazam  # to identify songs from short audio snippets
import pandas as pd   # to build DataFrame and export CSV
from dotenv import load_dotenv  # to read .env file into os.environ

# Load environment variables from .env file
load_dotenv()

#Retrieve Instragram username and password from environment variables
IG_USERNAME = os.getenv('INSTAGRAM_USERNAME')
IG_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# Sanity check if username and password are provided
if not IG_USERNAME or not IG_PASSWORD:
    raise EnvironmentError(
        "Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file."
        )

# Create instance of Instaloader, we disable viedo/picture download options since we only need URLs
loader = instaloader.Instaloader(download_pictures=False, download_videos=False, save_metadata=False)

# Attempt to load a saved session (if previously logged in). If not, we do an interactive login.
try:
    loader.load_session_from_file(IG_USERNAME)
    print(f"[INFO] Loaded existing session for Instagram user '{IG_USERNAME}'.")
except FileNotFoundError:
    # No stored session file, so perform a fresh login
    print(f"[INFO] No existing session found for '{IG_USERNAME}'. Logging in now...")
    loader.login(IG_USERNAME, IG_PASSWORD)
    # After successful login, Instaloader will save a session file in ~/.config/instaloader/session-<username>
    loader.save_session_to_file()

print("[INFO] Instagram login successful.")

