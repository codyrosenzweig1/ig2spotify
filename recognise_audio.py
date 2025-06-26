import os
import sys
import csv
import datetime
import subprocess
import json

from dotenv import load_dotenv
from acrcloud.recognizer import ACRCloudRecognizer

# -------------------------
# ACRCloud Credentials & SDK Setup
# -------------------------
load_dotenv()  # loads ACR_HOST, ACR_ACCESS_KEY, ACR_ACCESS_SECRET from .env

ACR_HOST       = os.getenv("ACR_HOST")               # e.g. identify-ap-southeast-1.acrcloud.com
ACCESS_KEY     = os.getenv("ACR_ACCESS_KEY")
ACCESS_SECRET  = os.getenv("ACR_ACCESS_SECRET")
RECOGNITION_LOG = "recognition_log.csv"

# Configure the SDK once, with a 10 s timeout
_reco_config = {
    "host":           ACR_HOST,
    "access_key":     ACCESS_KEY,
    "access_secret":  ACCESS_SECRET,
    "timeout":        10,
}
_recognizer = ACRCloudRecognizer(_reco_config)

# -------------------------
# Utility: Which files we've already logged
# -------------------------
def get_logged_files() -> set[str]:
    """
    Reads the CSV log and returns the set of file names already processed.
    """
    if not os.path.exists(RECOGNITION_LOG):
        return set()
    with open(RECOGNITION_LOG, newline="", encoding="utf-8") as f:
        return {row[1] for row in csv.reader(f) if row}

# -------------------------
# Utility: Append one result row to the log
# -------------------------
def log_result(file_name: str, status: str, title: str = "", artist: str = "", source: str = "") -> None:
    """
    Appends a line to recognition_log.csv with:
      timestamp, file_name, title, artist, source/status
    """
    with open(RECOGNITION_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(),
            file_name,
            title,
            artist,
            source or status
        ])

# -------------------------
# Trim & Convert Audio to Last 20 Seconds
# -------------------------
def convert_and_trim(file_path: str) -> str | None:
    """
    - Uses ffprobe to get total duration.
    - Calculates `start = max(0, duration - 20)` so we capture the final 20 s.
    - Runs ffmpeg to extract that 20 s and transcode to MP3.
    - If original was .mp4, replaces it with the new .mp3.
    Returns the path to the MP3 to send to ACRCloud, or None on failure.
    """
    base, ext = os.path.splitext(file_path)
    is_mp4 = ext.lower() == ".mp4"
    trimmed = f"{base}_trimmed.mp3"

    try:
        # ——— 1) Probe for total duration ———
        p = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ], capture_output=True, text=True)

        out = p.stdout.strip()
        if not out:
            print(f"⚠️ ffprobe returned nothing for {file_path}, defaulting duration=0")
            duration = 0.0
        else:
            duration = float(out)

        # ——— 2) Compute start time to get last 20 s ———
        start = max(0, duration - 20)

        # ——— 3) Run ffmpeg to trim & transcode ———
        ff = subprocess.run([
            "ffmpeg", "-y", "-i", file_path,
            "-ss", str(start), "-t", "20",
            "-vn", "-acodec", "libmp3lame", trimmed
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Validation: check exit code, file exists and has size
        if ff.returncode != 0 or not os.path.exists(trimmed) or os.path.getsize(trimmed) < 1000:
            print(f"❌ ffmpeg failed ({ff.returncode}): {ff.stderr.decode()}")
            return None

        # If original was MP4, replace it
        if is_mp4:
            os.remove(file_path)
            final = base + ".mp3"
            os.rename(trimmed, final)
            print(f"🔁 Converted & trimmed: {final}")
            return final

        return trimmed

    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return None

# -------------------------
# ACRCloud Recognition via SDK
# -------------------------
def recognise_audio(file_path: str) -> dict | None:
    """
    Sends the first (up to) 20 s of audio to ACRCloud and returns the parsed JSON dict.
    If the SDK returns a JSON-string, we parse it; on errors, return None.
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None

    # SDK call: recognize_by_file(path, offset_s, duration_s)
    raw = _recognizer.recognize_by_file(file_path, 0, 20)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("❌ Failed to parse SDK JSON:", raw)
        return None

# -------------------------
# Process One File
# -------------------------
def process_file(original_file: str) -> None:
    """
    1) Skip if already logged.
    2) Convert/trim to MP3 (last 20 s).
    3) Call ACRCloud SDK → parse result.
    4) Append SUCCESS / NO_MATCH / errors to CSV.
    """
    name = os.path.basename(original_file)
    if name in get_logged_files():
        print(f"⏭️ Skipping already processed: {name}")
        return

    print(f"🎧 Processing: {name}")

    proc = convert_and_trim(original_file)
    if not proc:
        log_result(name, "PREPROCESS_FAILED")
        return

    res = recognise_audio(proc)

    # Clean up trimmed temp
    if proc != original_file and proc.endswith("_trimmed.mp3"):
        os.remove(proc)

    if not res:
        log_result(name, "RECOGNITION_FAILED")
        return

    status = res.get("status", {}).get("msg", "")
    if status == "Success":
        m      = res["metadata"]["music"][0]
        title  = m.get("title", "")
        artist = m.get("artists", [{}])[0].get("name", "")
        log_result(name, "SUCCESS", title, artist, "ACRCloud")
        print(f"✅ Recognised: {title} – {artist}")
    else:
        log_result(name, "NO_MATCH")
        print(f"❌ No match: {name}")

# -------------------------
# Process a Directory of Files
# -------------------------
def process_directory(dir_path: str) -> None:
    """
    Iterate over all .mp3/.mp4 files, sorted alphabetically,
    and call process_file() on each.
    """
    print(f"📂 Scanning: {dir_path}")
    for f in sorted(os.listdir(dir_path)):
        if f.lower().endswith((".mp3", ".mp4")):
            process_file(os.path.join(dir_path, f))

# -------------------------
# Entry Point
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python recognise_audio.py <file_or_folder>")
        sys.exit(1)

    path = sys.argv[1]
    if os.path.isdir(path):
        process_directory(path)
    else:
        process_file(path)
