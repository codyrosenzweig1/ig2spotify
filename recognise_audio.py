import os
import sys
import csv
import time
import hmac
import base64
import hashlib
import json
import requests
import datetime
import subprocess
from dotenv import load_dotenv

# -------------------------
# ACRCloud Credentials
# -------------------------
load_dotenv()
ACR_HOST      = os.getenv('ACR_HOST')                  # e.g. identify-ap-southeast-1.acrcloud.com
ACR_ENDPOINT  = f"https://{ACR_HOST}/v1/identify"
ACCESS_KEY    = os.getenv('ACR_ACCESS_KEY')
ACCESS_SECRET = os.getenv('ACR_ACCESS_SECRET')
RECOGNITION_LOG = 'recognition_log.csv'

# -------------------------
# Utility: Load logged files
# -------------------------
def get_logged_files():
    if not os.path.exists(RECOGNITION_LOG):
        return set()
    with open(RECOGNITION_LOG, 'r', newline='', encoding='utf-8') as f:
        return {row[1] for row in csv.reader(f) if row}

# -------------------------
# Utility: Append to CSV
# -------------------------
def log_result(file_name, status, title='', artist='', source=''):
    with open(RECOGNITION_LOG, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(),
            file_name,
            title,
            artist,
            source or status
        ])

# -------------------------
# Trim & Convert Audio
# -------------------------
def convert_and_trim(file_path):
    base, ext = os.path.splitext(file_path)
    is_mp4 = ext.lower() == '.mp4'
    trimmed_file = f"{base}_trimmed.mp3"

    try:
        # Get duration
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ], capture_output=True, text=True)
        duration = float(result.stdout.strip())
        start_time = max(0, duration - 20)

        # Convert and trim
        ff = subprocess.run([
            "ffmpeg", "-y", "-i", file_path,
            "-ss", str(start_time), "-t", "20",
            "-vn", "-acodec", "libmp3lame", trimmed_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if ff.returncode != 0 or not os.path.exists(trimmed_file) or os.path.getsize(trimmed_file) < 1000:
            print(f"❌ ffmpeg failed: {ff.stderr.decode()}")
            return None

        # Replace .mp4 with .mp3
        if is_mp4:
            os.remove(file_path)
            final = base + ".mp3"
            os.rename(trimmed_file, final)
            print(f"🔁 Converted and trimmed: {final}")
            return final
        return trimmed_file

    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return None

# -------------------------
# ACRCloud Request
# -------------------------
def recognise_audio(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None

    size = os.path.getsize(file_path)
    if size < 1000:
        print(f"⚠️ File too small: {file_path}")
        return None

    with open(file_path, 'rb') as f:
        data = f.read()

    timestamp = str(int(time.time()))
    signature_version = "1"
    string_to_sign = "\n".join([
        "POST",
        "/v1/identify",
        ACCESS_KEY,
        "audio",
        signature_version,
        timestamp
    ])
    sign = base64.b64encode(
        hmac.new(ACCESS_SECRET.encode('ascii'),
                 string_to_sign.encode('ascii'),
                 digestmod=hashlib.sha1).digest()
    ).decode('ascii')

    headers = {
        "access-key":        ACCESS_KEY,
        "signature":         sign,
        "timestamp":         timestamp,
        "data-type":         "audio",
        "signature-version": signature_version,
    }

    print(f"📤 Sending {os.path.basename(file_path)} ({size} bytes)...")
    response = requests.post(ACR_ENDPOINT, headers=headers, files={'sample': data})
    print(f"🔄 Status: {response.status_code}")

    try:
        result = response.json()
        print(f"📬 Response: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        return None

# -------------------------
# Recognition Logic
# -------------------------
def process_file(original_file):
    name = os.path.basename(original_file)
    if name in get_logged_files():
        print(f"⏭️ Skipping already processed: {name}")
        return

    print(f"🎧 Processing: {name}")
    proc = convert_and_trim(original_file)
    if not proc:
        log_result(name, 'PREPROCESS_FAILED')
        return

    res = recognise_audio(proc)
    # Clean up trimmed if applicable
    if proc != original_file and proc.endswith("_trimmed.mp3"):
        os.remove(proc)

    if not res:
        log_result(name, 'RECOGNITION_FAILED')
    elif res.get("status", {}).get("msg") == "Success":
        m = res["metadata"]["music"][0]
        title = m.get("title", "")
        artist = m.get("artists", [{}])[0].get("name", "")
        log_result(name, 'SUCCESS', title, artist, 'ACRCloud')
        print(f"✅ Got: {title} – {artist}")
    else:
        log_result(name, 'NO_MATCH')
        print(f"❌ No match: {name}")

# -------------------------
# Batch Logic
# -------------------------
def process_directory(dir_path):
    print(f"📂 Scanning: {dir_path}")
    exts = ('.mp3', '.mp4')
    for f in sorted(os.listdir(dir_path)):
        if f.endswith(exts):
            process_file(os.path.join(dir_path, f))

# -------------------------
# Entry Point
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python recognise_audio.py <file_or_folder>")
        sys.exit(1)
    p = sys.argv[1]
    if os.path.isdir(p):
        process_directory(p)
    else:
        process_file(p)
