import sys
import os

# Ensure we can import spotify_integration
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from spotify_integration.auth import get_spotify_client
from spotify_integration.csv_reader import load_recognised_songs_from_csv
from spotify_integration.search_tracks import search_spotify_track

sp = get_spotify_client()
songs = load_recognised_songs_from_csv("recognition_log.csv")

print(f"🎧 Loaded {len(songs)} recognised songs from log.")

for i, (title, artist) in enumerate(songs, 1):
    print(f"\n[{i}/{len(songs)}] 🔍 Searching: {title} – {artist}")
    uri = search_spotify_track(sp, title, artist)
    if uri:
        print(f"✅ URI: {uri}")
    else:
        print("❌ Not found on Spotify.")
