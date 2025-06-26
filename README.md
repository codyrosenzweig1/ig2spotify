A fully-automated Python pipeline that:

1. **Downloads** Instagram Reels audio (via Selenium-Wire)  
2. **Extracts** only the final 20 seconds of each clip  
3. **Recognises** songs using the ACRCloud Python SDK  
4. **Logs** results in a robust CSV (`recognition_log.csv`)  
5. **Adds** recognised tracks to a Spotify playlist

---

## 🚀 Quickstart

1. **Clone & install dependencies**  
   ```bash
   git clone https://github.com/yourusername/ig2spotify.git
   cd ig2spotify
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
Configure
Copy .env.example to .env and fill in your credentials:

dotenv
Copy
Edit
IG_USERNAME=your_instagram_username
IG_PASSWORD=your_instagram_password

ACR_HOST=identify-ap-southeast-1.acrcloud.com
ACR_ACCESS_KEY=your_acrcloud_access_key
ACR_ACCESS_SECRET=your_acrcloud_secret

SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
Run the full pipeline

bash
Copy
Edit
python full_pipeline.py <instagram_username> [spotify_playlist_name]
<instagram_username>: the target IG account

[spotify_playlist_name]: optional; defaults to ig2spotify

What happens?

Step 1: Reels are downloaded (audio-only) via Selenium-Wire

Step 2: Each file is trimmed to its final 20 s and converted to MP3

Step 3: Clips are sent to ACRCloud SDK for recognition

Step 4: Results are appended to recognition_log.csv

Step 5: Recognised tracks are searched on Spotify and added to your playlist

📁 Project Structure
graphql
Copy
Edit
.
├── full_pipeline.py
├── selenium_wire_download_reels.py  # grabs IG Reel audio packets
├── recognise_audio.py              # trims & recognises via ACRCloud SDK
├── csv_reader.py                   # ensures & loads the log CSV
├── spotify_integration/  
│   ├── auth.py                     # Spotify OAuth helper
│   ├── search_tracks.py            # track-search logic
│   └── playlist_manager.py         # create/find playlist & add tracks
├── recognition_log.csv             # master log of recognitions (+ URIs)
├── requirements.txt
├── .env.example
└── README.md
🔍 How It Works
1. Downloading Reels
Selenium-Wire logs into Instagram and navigates to the target account’s Reels feed.

It intercepts the audio stream URLs and downloads only the audio packets.

2. Extracting the Last 20 Seconds
bash
Copy
Edit
# Pseudocode inside recognise_audio.py
duration = ffprobe(file.mp4)
start    = max(0, duration – 20)
ffmpeg –ss $start –t 20 –i file.mp4 file_trimmed.mp3
Focusing on the end of the clip maximises the chance of capturing the song’s core section.

3. Recognising Songs
The ACRCloud SDK (recognize_by_file(path, 0, 20)) handles HMAC signing, multipart uploads, and error handling.

On success, we extract title and artist and log alongside a timestamp.

4. CSV Logging
recognition_log.csv is auto-created (with headers) on first run.

Each row:

bash
Copy
Edit
timestamp, file_name, title, artist, source, spotify_uri
spotify_uri is appended after the Spotify integration step.

5. Spotify Playlist Integration
We read the CSV, filter successful entries, and search each track via the Spotify Web API.

Unique URIs are added to a playlist (default name ig2spotify).