import pandas as pd

def load_recognition_log_as_df(csv_path: str) -> pd.DataFrame:
    """
    Loads the recognition log into a pandas DataFrame.
    Filters to keep only successful ACRCloud results with both title and artist.
    """
    try:
        df = pd.read_csv(csv_path)

        # Ensure required columns exist
        required_cols = {'title', 'artist', 'source'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing columns in CSV: {missing}")

        # Filter valid entries
        df = df[
            (df["title"].notna()) &
            (df["artist"].notna()) &
            (df["title"].str.strip() != "") &
            (df["artist"].str.strip() != "") &
            (df["source"] == "ACRCloud")
        ].copy()

        return df.reset_index(drop=True)

    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return pd.DataFrame()
