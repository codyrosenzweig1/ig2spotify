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

ACR_HOST = os.getenv('ACR_HOST')
ACCESS_KEY = os.getenv('ACR_ACCESS_KEY')
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
# Trim & Convert Audio (if needed)
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

        # Convert and trim audio
        result = subprocess.run([
            "ffmpeg", "-y", "-i", file_path,
            "-ss", str(start_time), "-t", "20",
            "-vn", "-acodec", "libmp3lame", trimmed_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            print(f"⚠️ ffmpeg exited with code {result.returncode} — stderr:\n{result.stderr.decode()}")

        if not os.path.exists(trimmed_file) or os.path.getsize(trimmed_file) < 1000:
            print(f"❌ ffmpeg failed or produced invalid file: {trimmed_file}")
            return None

        # If file was originally .mp4, delete it and rename trimmed file
        if is_mp4:
            os.remove(file_path)
            final_path = base + ".mp3"
            os.rename(trimmed_file, final_path)
            print(f"🔁 Replaced .mp4 with trimmed .mp3: {final_path}")
            return final_path
        else:
            return trimmed_file

    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        return None

# -------------------------
# ACRCloud Request
# -------------------------
def recognize_audio(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None

        file_size = os.path.getsize(file_path)
        if file_size < 1000:
            print(f"⚠️ File too small or empty: {file_path} ({file_size} bytes)")
            return None

        with open(file_path, 'rb') as f:
            data = f.read()

        timestamp = str(int(time.time()))
        string_to_sign = '\n'.join([
            'POST', '/v1/identify', ACCESS_KEY, 'audio', timestamp
        ])
        sign = base64.b64encode(
            hmac.new(ACCESS_SECRET.encode('ascii'),
                     string_to_sign.encode('ascii'),
                     digestmod=hashlib.sha1).digest()
        ).decode('ascii')

        headers = {
            'access-key': ACCESS_KEY,
            'signature': sign,
            'timestamp': timestamp,
            'data-type': 'audio',
            'signature-version': '1',
        }

        print(f"📤 Sending {os.path.basename(file_path)} to ACRCloud ({file_size} bytes)...")
        response = requests.post(ACR_HOST, headers=headers, files={'sample': data})

        print(f"🔄 Status Code: {response.status_code}")
        try:
            result_json = response.json()
            print(f"📬 Response: {json.dumps(result_json, indent=2)}")
            return result_json
        except Exception as parse_err:
            print(f"❌ Could not parse JSON: {parse_err}")
            return None

    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

# -------------------------
# Recognition Logic
# -------------------------
def process_file(original_file):
    file_name = os.path.basename(original_file)
    if file_name in get_logged_files():
        print(f"⏭️  Skipping already recognised file: {file_name}")
        return

    print(f"🎧 Processing: {file_name}")

    processed_file = convert_and_trim(original_file)
    if not processed_file:
        log_result(file_name, 'PREPROCESS_FAILED')
        return

    result = recognize_audio(processed_file)

    # If we created a temp trimmed mp3 (not replacement), clean it up
    if processed_file != original_file and processed_file.endswith("_trimmed.mp3"):
        os.remove(processed_file)

    if not result:
        log_result(file_name, 'RECOGNITION_FAILED')
        return

    if result.get('status', {}).get('msg') == 'Success':
        metadata = result['metadata']['music'][0]
        title = metadata.get('title', '')
        artist = metadata.get('artists', [{}])[0].get('name', '')
        log_result(file_name, 'SUCCESS', title, artist, 'ACRCloud')
        print(f"✅ Recognised: {title} - {artist}")
    else:
        log_result(file_name, 'NO_MATCH')
        print(f"❌ No match for: {file_name}")

# -------------------------
# Batch Folder Logic
# -------------------------
def process_directory(directory):
    print(f"📂 Scanning folder: {directory}")
    supported_exts = ('.mp3', '.mp4')
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(supported_exts)]
    for file_path in sorted(files):
        process_file(file_path)

# -------------------------
# Entry Point
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python recognise_audio.py <file_or_folder_path>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print("❌ Path not found.")
        sys.exit(1)

    if os.path.isdir(path):
        process_directory(path)
    else:
        process_file(path)
