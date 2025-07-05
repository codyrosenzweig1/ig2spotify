import os
import pandas as pd

from spotify_integration.auth import get_spotify_client
from spotify_integration.csv_reader import write_current, read_history
from spotify_integration.playlist_manager import get_or_create_playlist, add_tracks_to_playlist
from spotify_integration.search_tracks import search_spotify_track

from backend.selenium_wire_download_reels import download_user_reels
from backend.batch_recognise import batch_process

# Use the history CSV maintained by csv_reader
RECOGNITION_LOG_PATH = 'recognition_history.csv'
DOWNLOAD_DIR = 'downloaded_reels'
DEFAULT_PLAYLIST_NAME = 'ig2spotify'
# RUN_ID = uuid.uuid4().hex

# Clear current-run if you're using read_current elsewhere;
# here we rely on history only, so only write_current([]) if needed for current
write_current([])


def run_full_pipeline(instagram_username: str, playlist_name: str = DEFAULT_PLAYLIST_NAME, limit: int = 10, run_id: str = None):
    print(f"🚀 Starting full pipeline for Instagram account: {instagram_username}")

    # Step 1: Download reels
    user_dir = os.path.join(DOWNLOAD_DIR, instagram_username)
    os.makedirs(user_dir, exist_ok=True)
    print("📹 Downloading reels...")
    download_user_reels(instagram_username, limit)

    # Step 2: Recognise audio
    print("🎧 Recognising audio...")
    batch_process(user_dir)

    # Step 3: Load Spotify client
    print("🔑 Logging into Spotify...")
    sp = get_spotify_client()

    # Step 4: Read recognition history
    print("📥 Loading recognition log...")
    df = read_history(RECOGNITION_LOG_PATH)

    # Replace NaN with empty strings for consistency
    df['title'] = df['title'].fillna('').astype(str)
    df['artist'] = df['artist'].fillna('').astype(str)
    df['spotify_uri'] = df['spotify_uri'].fillna('').astype(str)

    if df.empty:
        print("⚠️ No recognised rows found.")
        return

    unmatched = df[df['spotify_uri'].isna() | (df['spotify_uri'].str.strip() == '')]
    if unmatched.empty:
        print("🎵 All tracks are already matched.")
        return

    # Step 5: Search Spotify for URIs
    new_uris = []
    for idx, row in unmatched.iterrows():
        title, artist = row['title'], row['artist']
        print(f"🔍 Searching: {title} – {artist}")
        if (title or artist) != '': 
            uri = search_spotify_track(sp, title, artist)
            if uri:
                print(f"✅ Found URI: {uri}")
                df.at[idx, 'spotify_uri'] = uri
                new_uris.append(uri)
            else:
                print("❌ No match found.")
        else:
            print("❌ No search completed, missing artist or title.")

    # Step 6: Add to playlist
    if new_uris:
        playlist_id = get_or_create_playlist(sp, playlist_name)
        add_tracks_to_playlist(sp, playlist_id, new_uris)
    else:
        print("🎵 No new tracks found to add.")

    # Step 7: Save updated history log
    df.to_csv(RECOGNITION_LOG_PATH, index=False)
    print("💾 Updated recognition history CSV")


# if __name__ == '__main__':
#     run_full_pipeline(TARGET_PROFILE)
