import io
from datetime import date, datetime

import pandas as pd

REQUIRED_COLUMNS = {"mobile", "product_name", "poll_date", "vote"}


def parse_poll_csv(raw_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw_bytes))
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

    df["mobile"] = df["mobile"].astype(str).str.strip()
    df["vote"] = df["vote"].astype(str).str.strip().str.lower()
    df["poll_date"] = pd.to_datetime(df["poll_date"].astype(str).str.strip(), format="mixed").dt.date
    return df


def parse_poll_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()
