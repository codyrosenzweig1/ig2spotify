## Here we will manage the creation and management of Spotify playlists
from spotipy import Spotify

def get_or_create_playlist(sp: Spotify, name, instagram_username, description="", public=False):
    """
    Get an existing playlist or create a new one if it doesn't exist.
    Returns the playlist object.
    """
    current_user_id = sp.current_user()['id']
    
    # Check for existing playlists
    playlists = sp.current_user_playlists(limit=50)
    for playlist in playlists['items']:
        if playlist['name'].lower() == "ig2spotify_{instagram_username}".lower():
            print(f"🎵 Found existing playlist: {playlist['name']}")
            return playlist['id']
    
    # Create a new playlist
    print("🎵 No existing playlist found, creating new playlist: {name}")
    new_playlist = sp.user_playlist_create(current_user_id, name=name, public=public, description=description)
    return new_playlist['id']

def add_tracks_to_playlist(sp: Spotify, playlist_id, track_uris) -> None:
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
        return
    
    print(f"🎵 Adding {len(new_tracks)} new tracks to playlist: {playlist_id}")
    sp.playlist_add_items(playlist_id, new_tracks)
    print(f"✅ Tracks added successfully")

