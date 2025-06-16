import spotipy
import urllib.parse

def search_spotify_track(sp, title, artist):
    """
    Searches Spotify for a given title and artist.
    Returns the track URI if found, else None.
    """
    try:
        # Build a clean, specific search query
        query = f'track:{title} artist:{artist}'
        print(f"🔍 Searching for: {query}")

        results = sp.search(q=query, type='track', limit=5)

        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            print("❌ No match found.")
            return None

        # Simple heuristic: return the top result
        top_track = tracks[0]
        track_uri = top_track['uri']
        print(f"✅ Found: {top_track['name']} – {top_track['artists'][0]['name']} [URI: {track_uri}]")
        return track_uri

    except Exception as e:
        print(f"❌ Spotify search failed: {e}")
        return None

# Test block
if __name__ == "__main__":
    from auth import get_spotify_client
    sp = get_spotify_client()

    # Example test
    title = "Opus"
    artist = "Eric Prydz"
    uri = search_spotify_track(sp, title, artist)
    print(f"URI: {uri}")
