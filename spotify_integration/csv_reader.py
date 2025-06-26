import os
import pandas as pd


def ensure_log_exists(csv_path: str, required_cols=None) -> None:
    """
    Ensure the recognition log CSV exists with the correct headers.
    Creates the file if missing, and adds any missing columns if the file exists.
    """
    if required_cols is None:
        required_cols = ['timestamp', 'file_name', 'title', 'artist', 'source', 'spotify_uri']

    if not os.path.exists(csv_path):
        # Create new CSV with headers
        df_empty = pd.DataFrame(columns=required_cols)
        df_empty.to_csv(csv_path, index=False)
        print(f"ℹ️ Created new recognition log with headers: {required_cols}")
    else:
        # Read existing and add missing columns
        df = pd.read_csv(csv_path, dtype=str)
        updated = False
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
                updated = True
                print(f"⚠️ Added missing column '{col}' to recognition log.")
        if updated:
            # Reorder columns
            df = df[required_cols]
            df.to_csv(csv_path, index=False)


def load_recognition_log_as_df(csv_path: str) -> pd.DataFrame:
    """
    Loads the full recognition log into a pandas DataFrame.
    Ensures the CSV exists with headers.
    """
    ensure_log_exists(csv_path)
    return pd.read_csv(csv_path, dtype=str)


def load_successful_recognitions(csv_path: str) -> pd.DataFrame:
    """
    Returns only the successful ACRCloud recognitions (title & artist present, source 'ACRCloud').
    """
    df = load_recognition_log_as_df(csv_path)
    if df.empty:
        return df

    # Filter valid entries: only where ACRCloud succeeded
    mask = (
        df['source'] == 'ACRCloud'
        & df['title'].notna() & df['artist'].notna()
        & (df['title'].str.strip() != '') & (df['artist'].str.strip() != '')
    )
    df_valid = df[mask].copy().reset_index(drop=True)
    return df_valid


# Quick test
if __name__ == '__main__':
    CSV_PATH = 'recognition_log.csv'
    df_full = load_recognition_log_as_df(CSV_PATH)
    print(df_full.head())
    df_success = load_successful_recognitions(CSV_PATH)
    print("✅ Successful recognitions:")
    print(df_success)
