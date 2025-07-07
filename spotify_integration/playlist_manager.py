## Here we will manage the creation and management of Spotify playlists
from spotipy import Spotify
from backend.app.main import PROGRESS_DATA

def get_or_create_playlist(sp: Spotify, playlist_name, instagram_username, runId, description="", public=False):
    """ 
    Get an existing playlist or create a new one if it doesn't exist.
    Returns the playlist object.
    """
    current_user_id = sp.current_user()['id']
    
    # Check for existing playlists
    playlists = sp.current_user_playlists(limit=50)
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            print(f"🎵 Found existing playlist: {playlist['name']}")
            return playlist['id']
    
    # Create a new playlist
    print(f"🎵 No existing playlist found, creating new playlist: {playlist_name}")
    new_playlist = sp.user_playlist_create(current_user_id, name=playlist_name, public=public, description=description)
    playlist_url = new_playlist['external_urls']['spotify']

    PROGRESS_DATA[runId]['playlist_url'] = playlist_url

    return new_playlist['id']

def add_tracks_to_playlist(sp: Spotify, playlist_id, track_uris, runId) -> None:
    """
    Add tracks to a specified playlist.
    """
    # Remove duplicates
    track_urls = list(dict.fromkeys(track_uris))

    # get current tracks in playlist
    existing_uris = set()
    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results['items']:
            existing_uris.add(item['track']['uri'])
        if results['next']:
            results = sp.next(results)
        else:
            break

    # Filter only new tracks
    new_tracks = [uri for uri in track_urls if uri not in existing_uris]
    if not new_tracks:
        print("🎵 No new tracks to add.")
        PROGRESS_DATA[runId]["tracks_matched"] += len(new_tracks)
        PROGRESS_DATA[runId]["playlist_done"] = True
        return
    
    print(f"🎵 Adding {len(new_tracks)} new tracks to playlist: {playlist_id}")
    sp.playlist_add_items(playlist_id, new_tracks)
    PROGRESS_DATA[runId]["tracks_matched"] += len(new_tracks)
    PROGRESS_DATA[runId]["playlist_done"] = True
    print(f"✅ Tracks added successfully")
    return # Unsure if this is needed

