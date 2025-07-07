import os
import sys
import datetime
import subprocess
import json
import uuid
from dotenv import load_dotenv
from acrcloud.recognizer import ACRCloudRecognizer
from spotify_integration.csv_reader import append_history, write_current, read_history
from backend.app.main import PROGRESS_DATA

# -----------------------------------------------------------------------------
# Run ID & Current Records
# -----------------------------------------------------------------------------
# # Unique identifier for this batch run (folder or single file)
RUN_ID = PROGRESS_DATA.get('runId')
# Accumulator for this run's records
current_records = []

# -----------------------------------------------------------------------------
# Initialize current-run CSV (clears previous contents)
# -----------------------------------------------------------------------------
# write_current([])

# -----------------------------------------------------------------------------
# Load ACRCloud credentials and instantiate the SDK
# -----------------------------------------------------------------------------
load_dotenv()  # loads ACR_HOST, ACR_ACCESS_KEY, ACR_ACCESS_SECRET from .env
ACR_HOST      = os.getenv("ACR_HOST")
ACCESS_KEY    = os.getenv("ACR_ACCESS_KEY")
ACCESS_SECRET = os.getenv("ACR_ACCESS_SECRET")
RECOG_CONFIG = {
    "host":           ACR_HOST,
    "access_key":     ACCESS_KEY,
    "access_secret":  ACCESS_SECRET,
    "timeout":        10,
}
_recognizer = ACRCloudRecognizer(RECOG_CONFIG)

# -----------------------------------------------------------------------------
# Utility: Which files we've already logged (history)
# -----------------------------------------------------------------------------
def get_logged_files() -> set[str]:
    """
    Return set of file names already present in recognition_history.csv.
    """
    df = read_history()
    return set(df['file_name'].fillna('').tolist())

# -----------------------------------------------------------------------------
# Trim & Convert Audio to Last 20 Seconds
# -----------------------------------------------------------------------------
def convert_and_trim(file_path: str) -> str | None:
    """
    - Uses ffprobe to get total duration.
    - Calculates `start = max(0, duration - 20)` to capture final 20s.
    - Runs ffmpeg to extract that segment to MP3.
    - If original was .mp4, replaces it.
    Returns the path to the MP3 or None on failure.
    """
    base, ext = os.path.splitext(file_path)
    is_mp4 = ext.lower() == ".mp4"
    trimmed = f"{base}_trimmed.mp3"

    try:
        # Probe for duration
        p = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ], capture_output=True, text=True)
        out = p.stdout.strip()
        duration = float(out) if out else 0.0

        start = max(0, duration - 20)
        ff = subprocess.run([
            "ffmpeg", "-y", "-i", file_path,
            "-ss", str(start), "-t", "20",
            "-vn", "-acodec", "libmp3lame", trimmed
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if ff.returncode != 0 or not os.path.exists(trimmed) or os.path.getsize(trimmed) < 1000:
            print(f"❌ ffmpeg failed ({ff.returncode}): {ff.stderr.decode()}")
            return None

        if is_mp4:
            os.remove(file_path)
            final = base + ".mp3"
            os.rename(trimmed, final)
            print(f"🔁 Converted & trimmed: {final}")
            PROGRESS_DATA[RUN_ID]['audio_converted'] += 1
            return final
        PROGRESS_DATA[RUN_ID]['audio_converted'] += 1
        return trimmed

    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return None

# -----------------------------------------------------------------------------
# ACRCloud Recognition via SDK
# -----------------------------------------------------------------------------
def recognise_audio(file_path: str) -> dict | None:
    """
    Uses ACRCloud SDK to identify a 20s snippet from `file_path`. Returns JSON dict or None.
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None

    raw = _recognizer.recognize_by_file(file_path, 0, 20)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("❌ Failed to parse SDK JSON:", raw)
        return None

# -----------------------------------------------------------------------------
# Process One File
# -----------------------------------------------------------------------------
def process_file(original_file: str, runId: str) -> None:
    name = os.path.basename(original_file)
    if name in get_logged_files():
        print(f"⏭️ Skipping already processed: {name}")
        return

    print(f"🎧 Processing: {name}")
    # proc = convert_and_trim(original_file)
    proc = original_file
    if not proc:
        status = 'PREPROCESS_FAILED'
        title = artist = ''
    else:
        res = recognise_audio(proc)
        # clean up trimmed temp
        if proc != original_file and proc.endswith('_trimmed.mp3'):
            os.remove(proc)

        if not res:
            status = 'RECOGNITION_FAILED'
            title = artist = ''
        else:
            msg = res.get('status', {}).get('msg', '')
            if msg == 'Success':
                m = res['metadata']['music'][0]
                title  = m.get('title', '')
                artist = m.get('artists', [{}])[0].get('name', '')
                status = 'SUCCESS'
            else:
                status = 'NO_MATCH'
                title = artist = ''

    # Build the uniform record for CSV
    record = {
        'timestamp':   datetime.datetime.now().isoformat(),
        'file_name':   name,
        'title':       title,
        'artist':      artist,
        'source':      status,
        'spotify_uri': '',                    # for phase 2
        'account':     os.getenv('TARGET_INSTAGRAM', ''),
        'run_id':      runId
    }

    # Append into history and accumulate for current
    append_history([record])
    current_records.append(record)


    # Console feedback
    if status == 'SUCCESS':
        print(f"✅ Recognised: {title} – {artist}")
    elif status == 'NO_MATCH':
        print(f"❌ No match: {name}")
    else:
        print(f"❌ {status}: {name}")
# -----------------------------------------------------------------------------
# Process Directory
# -----------------------------------------------------------------------------
def process_directory(dir_path: str) -> None:
    print(f"📂 Scanning: {dir_path}")
    for f in sorted(os.listdir(dir_path)):
        if f.lower().endswith(('.mp3', '.mp4')):
            process_file(os.path.join(dir_path, f))

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python recognise_audio.py <file_or_folder> <run_id>")
        sys.exit(1)

    path = sys.argv[1]
    runId = sys.argv[2]
    if os.path.isdir(path):
        process_directory(path)
    else:
        process_file(path, runId)

    # Write out the current-run CSV once everything's done
    write_current(current_records)
    print(f"✅ Done. History & current logs updated (run_id={RUN_ID})")