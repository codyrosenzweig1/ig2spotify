import csv

def load_recognised_songs_from_csv(csv_path):
    """
    Loads all recognised (SUCCESS) songs from the CSV log.
    Returns a list of (title, artist) tuples.
    """
    songs = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["title"] and row["artist"] and row["source"] == "ACRCloud":
                    if row["title"].strip() and row["artist"].strip():
                        songs.append((row["title"].strip(), row["artist"].strip()))
    except FileNotFoundError:
        print(f"❌ Could not find file: {csv_path}")
    except KeyError as e:
        print(f"❌ CSV missing expected column: {e}")
    return songs

# Quick test
if __name__ == "__main__":
    tracks = load_recognised_songs_from_csv("recognition_log.csv")
    for title, artist in tracks:
        print(f"🎵 {title} – {artist}")
