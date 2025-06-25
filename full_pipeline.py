import os
import time

from spotify_integration.auth import get_spotify_client
from spotify_integration.csv_reader import load_recognition_log_as_df
from spotify_integration.playlist_manager import get_or_create_playlist, add_tracks_to_playlist
from spotify_integration.search_tracks import search_spotify_track

from selenium_wire_download_reels import download_user_reels, TARGET_PROFILE
from batch_recognise import batch_process

RECOGNITION_LOG_PATH = "recognition_log.csv"
DOWNLOAD_DIR = "downloaded_reels"
DEFAULT_PLAYLIST_NAME = "ig2spotify"

def run_full_pipeline(instagram_username: str, playlist_name: str = DEFAULT_PLAYLIST_NAME):
    print(f"🚀 Starting full pipeline for Instagram account: {instagram_username}")

    # Step 1: Download reels
    user_dir = os.path.join(DOWNLOAD_DIR, instagram_username)
    os.makedirs(user_dir, exist_ok=True)

    print("📹 Downloading reels...")
    # download_user_reels(instagram_username)  # Function already creates folder internally

    # Step 2: Recognise audio
    print("🎧 Recognising audio...")
    batch_process(user_dir)  # Calls recognise_audio.py per file and logs result in CSV

    # Step 3: Load Spotify client
    print("🔑 Logging into Spotify...")
    sp = get_spotify_client()

    # Step 4: Read unmatched rows from CSV
    print("📥 Loading recognition log...")
    df = load_recognition_log_as_df(RECOGNITION_LOG_PATH)

    if df.empty:
        print("⚠️ No recognised rows found.")
        return

    unmatched = df[df["spotify_uri"].isna() | (df["spotify_uri"].str.strip() == "")]
    if unmatched.empty:
        print("🎵 All tracks are already matched.")
        return

    # Step 5: Search tracks and update URIs
    new_uris = []
    for idx, row in unmatched.iterrows():
        title, artist = row["title"], row["artist"]
        print(f"🔍 Searching: {title} – {artist}")
        uri = search_spotify_track(sp, title, artist)
        if uri:
            print(f"✅ Found URI: {uri}")
            df.at[idx, "spotify_uri"] = uri
            new_uris.append(uri)
        else:
            print("❌ No match found.")

    # Step 6: Add to playlist
    if new_uris:
        playlist_id = get_or_create_playlist(sp, playlist_name)
        add_tracks_to_playlist(sp, playlist_id, new_uris)
    else:
        print("🎵 No new tracks found to add.")

    # Step 7: Save log
    df.to_csv(RECOGNITION_LOG_PATH, index=False)
    print("💾 Updated recognition_log.csv")

if __name__ == "__main__":
    run_full_pipeline(TARGET_PROFILE)
