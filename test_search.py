import sys
import os

# Dynamically add project root to PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from spotify_integration.auth import get_spotify_client
from spotify_integration.search_tracks import search_spotify_track

# Simulated test entry from recognition_log.csv
title = "Opus"
artist = "Eric Prydz"

# Get authorised Spotify client
sp = get_spotify_client()

# Search
uri = search_spotify_track(sp, title, artist)

if uri:
    print(f"🎯 Track URI found: {uri}")
else:
    print("🔍 No track found.")
