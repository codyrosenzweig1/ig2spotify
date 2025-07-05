import os
import sys
import glob
import subprocess

RECOGNISE_SCRIPT = "backend/recognise_audio.py"

def batch_process(directory):
    if not os.path.exists(RECOGNISE_SCRIPT):
        print(f"❌ Could not find {RECOGNISE_SCRIPT}")
        return

    files = glob.glob(os.path.join(directory, "*.mp4")) + glob.glob(os.path.join(directory, "*.mp3"))
    files.sort()  # Optional: ensures consistent order

    print(f"🎧 Found {len(files)} files in {directory}")
    for i, file_path in enumerate(files):
        print(f"\n➡️  [{i+1}/{len(files)}] Processing: {file_path}")
        subprocess.run(["python", RECOGNISE_SCRIPT, file_path])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python batch_recognise.py /path/to/audio_or_video_folder")
        sys.exit(1)

    input_folder = sys.argv[1]
    if not os.path.isdir(input_folder):
        print("❌ Provided path is not a directory.")
        sys.exit(1)

    batch_process(input_folder)
