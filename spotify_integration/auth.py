import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env
load_dotenv()

def get_spotify_client():
    scope = "playlist-modify-private playlist-read-private"

    sp_oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=scope,
        cache_path=".cache-ig2spotify"
    )

    return spotipy.Spotify(auth_manager=sp_oauth)

# Optional test
if __name__ == "__main__":
    sp = get_spotify_client()
    user = sp.current_user()
    print(f"✅ Authenticated as: {user['display_name']} ({user['id']})")
