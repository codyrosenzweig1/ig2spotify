import os
import sys
import glob
import subprocess
from pathlib import Path
from backend.app.main import PROGRESS_DATA

PYTHON = sys.executable
MODULE = "backend.recognise_audio"

def batch_process(directory, runId):
    # make sure we're in the project room so imports work
    project_root = Path(__file__).parent.parent.resolve()

    files = glob.glob(os.path.join(directory, "*.mp4")) + glob.glob(os.path.join(directory, "*.mp3"))
    files.sort()  # Optional: ensures consistent order

    print(f"🎧 Found {len(files)} files in {directory}")
    for i, file_path in enumerate(files):
        print(f"\n➡️  [{i+1}/{len(files)}] Processing: {file_path}")
        subprocess.run(
            [PYTHON, "-m", MODULE, file_path, runId],
            cwd=project_root,
            check=True
        )
        PROGRESS_DATA[runId]['track_recognition_processed'] += 1
    
        

# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Usage: python batch_recognise.py /path/to/audio_or_video_folder")
#         sys.exit(1)

#     input_folder = sys.argv[1]
#     if not os.path.isdir(input_folder):
#         print("❌ Provided path is not a directory.")
#         sys.exit(1)

#     batch_process(input_folder, runId)
