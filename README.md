# ig2spotify

A Python-based tool to automatically extract songs from an Instagram user’s Reels, identify them via Shazam, and (optionally) compile them into a Spotify playlist. This project demonstrates end-to-end automation of:

1. **Scraping Instagram Reels** (without manual scrolling)  
2. **Extracting audio snippets** (without downloading full videos)  
3. **Identifying songs** using a Shazam-style API  
4. **Exporting results** into a CSV for review  
5. **(Future) Creating a Spotify playlist** from identified track URIs  

---

## 📝 Project Overview

Many Instagram users share music-driven Reels, but manually watching, “Shazaming,” and then building a playlist is tedious. This tool performs that whole workflow programmatically:

1. **Login & Fetch Reels**  
   - Use [Instaloader](https://instaloader.github.io/) to log in (once) and fetch every Reel’s direct video URL from a given profile.  
   - No headless‐browser scrolling or brittle HTML parsing is required.

2. **Audio Extraction**  
   - For each Reel, invoke **FFmpeg** to stream just 10–15 seconds of audio directly from the remote MP4 URL.  
   - This avoids downloading entire video files—only a small MP3 snippet is processed.

3. **Song Recognition (Shazamio)**  
   - Feed each audio snippet to [Shazamio](https://pypi.org/project/shazamio/), an unofficial Shazam‐wrapper, to obtain the track title, artist, and confidence score.  
   - Handle cases where no match is found.

4. **CSV Export**  
   - Aggregate all “Reel → Title → Artist → Confidence” data into a `reels_songs.csv` file.  
   - Review the CSV to confirm which songs were identified (or flagged as unknown).

5. **(Optional) Spotify Playlist Creation**  
   - In a second phase, read the CSV, look up each song on Spotify via its Web API, gather URIs, and programmatically create or update a Spotify playlist in your account.  
   - This phase is separate so you can verify recognition accuracy before pushing tracks to Spotify.

By splitting the project into two phases (CSV generation first, playlist creation later), you can validate results before making any changes to your Spotify account. Each step is clearly isolated, well‐documented, and uses robust libraries to minimize maintenance.

---

## 🔧 Tech Stack & Tools

- **Python 3.8+**  
- **Instaloader**: Programmatic access to Instagram’s private GraphQL endpoints for fetching Reels.  
- **FFmpeg**: Command-line tool (invoked via `asyncio`) to stream‐extract MP3 audio snippets from remote MP4 URLs.  
- **Shazamio**: Async Python wrapper for Shazam’s recognition API to identify songs from small audio clips.  
- **Pandas**: For assembling data into a DataFrame and exporting to CSV.  
- **python-dotenv**: Load environment variables (`.env`) containing Instagram/Spotify credentials.  
- **Spotipy** (future phase): A Python client for the Spotify Web API to create playlists and add tracks.  
- **Git & GitHub**: Version control and remote hosting for sharing your code (with a proper `.gitignore` in place).  
- **Virtual Environment**: Isolate project dependencies in `venv/`.

---