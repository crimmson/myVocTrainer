import pandas as pd

FILE = "phrases.xlsx"

def load_data():
    df = pd.read_excel(FILE)

    df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce")

    if "interval" not in df.columns:
        df["interval"] = 1

    if "next_review" not in df.columns:
        df["next_review"] = pd.Timestamp.today()

    if "status" not in df.columns:
        df["status"] = "new"

    df["interval"] = pd.to_numeric(df["interval"], errors="coerce").fillna(1).astype(int)
    df["interval"] = df["interval"].clip(upper=10)

    df["next_review"] = pd.to_datetime(df["next_review"], errors="coerce")

    return df


def save_data(df):
    df.to_excel(FILE, index=False)