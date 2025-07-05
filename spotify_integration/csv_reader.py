import os
import pandas as pd
from filelock import FileLock

# Columns required in both history and current CSVs
REQUIRED_COLS = [
    'timestamp',     # ISO timestamp of processing
    'file_name',     # Source file name or URL
    'title',         # Matched track title (empty if none)
    'artist',        # Matched artist name (empty if none)
    'source',        # Status or source code from ACRCloud
    'spotify_uri',   # URI from Spotify lookup (empty until phase 2)
    'account',       # Instagram account or profile identifier
    'run_id'         # Unique identifier for this pipeline run
]

DEFAULT_HISTORY_PATH = 'backend/logs/recognition_history.csv'
DEFAULT_CURRENT_PATH = 'backend/logs/recognition_current.csv'


def _ensure_csv(path: str) -> None:
    """
    Create the CSV with headers if missing, or add missing columns if exists.
    """
    if not os.path.exists(path):
        # New file: write only the required columns
        pd.DataFrame(columns=REQUIRED_COLS).to_csv(path, index=False)
    else:
        # Existing file: ensure all required columns are present
        df = pd.read_csv(path, dtype=str)
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            for c in missing:
                df[c] = ''
            df.to_csv(path, index=False)


def read_history(path: str = DEFAULT_HISTORY_PATH) -> pd.DataFrame:
    """Return the full history of processed clips."""
    _ensure_csv(path)
    lock = FileLock(path + '.lock')
    with lock:
        return pd.read_csv(path, dtype=str)


def append_history(records: list[dict], path: str = DEFAULT_HISTORY_PATH) -> None:
    """Append new records to the history CSV (ignores empty lists)."""
    if not records:
        return
    _ensure_csv(path)
    df_new = pd.DataFrame(records)
    lock = FileLock(path + '.lock')
    with lock:
        df = pd.read_csv(path, dtype=str)
        df = pd.concat([df, df_new], ignore_index=True)
        df.to_csv(path, index=False)


def write_current(records: list[dict], path: str = DEFAULT_CURRENT_PATH) -> None:
    """Overwrite the current-run CSV with only these records."""
    df_new = pd.DataFrame(records, columns=REQUIRED_COLS)
    lock = FileLock(path + '.lock')
    with lock:
        df_new.to_csv(path, index=False)


def read_current(path: str = DEFAULT_CURRENT_PATH) -> pd.DataFrame:
    """Return the records from the current run."""
    _ensure_csv(path)
    lock = FileLock(path + '.lock')
    with lock:
        return pd.read_csv(path, dtype=str)
