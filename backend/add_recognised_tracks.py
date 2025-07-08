import pandas as pd
from spotify_integration.auth import get_spotify_client
from spotify_integration.csv_reader import load_recognition_log_as_df
from spotify_integration.search_tracks import search_spotify_track
from spotify_integration.playlist_manager import get_or_create_playlist, add_tracks_to_playlist

RECOGNITION_CSV_PATH = "backend/logs/recognition_log.csv"
PLAYLIST_NAME = "ig2spotify"

def main():
    print("📥 Loading recognised tracks from recognition_log.csv")
    df_full = load_recognition_log_as_df(RECOGNITION_CSV_PATH)
    if df_full.empty:
        print("⚠️ No recognised tracks found.")
        return

    df_full = df_full.dropna(subset=["title", "artist"])

    # Find only unmatched
    df_unmatched = df_full[df_full["spotify_uri"].isna() | (df_full["spotify_uri"].str.strip() == "")]
    print(f"🔍 {len(df_unmatched)} unmatched tracks to process...")

    sp = get_spotify_client()
    playlist_id = get_or_create_playlist(sp, PLAYLIST_NAME)

    new_uris = []

    for idx, row in df_unmatched.iterrows():
        title = row["title"]
        artist = row["artist"]
        print(f"🎧 Searching: {title} – {artist}")

        uri = search_spotify_track(sp, title, artist)
        if uri:
            print(f"✅ Found match: {uri}")
            df_full.loc[idx, "spotify_uri"] = uri
            new_uris.append(uri)
        else:
            print("❌ No match found")

    if new_uris:
        add_tracks_to_playlist(sp, playlist_id, new_uris)
    else:
        print("🎵 No new tracks to add to playlist.")

    # Save full DataFrame, not just unmatched
    df_full.to_csv(RECOGNITION_CSV_PATH, index=False)
    print("💾 recognition_log.csv updated successfully.")

if __name__ == "__main__":
    main()
