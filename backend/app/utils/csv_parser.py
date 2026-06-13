import pandas as pd
import io

COLUMN_ALIASES = {
    "date": ["date", "transaction date", "txn date", "value date"],
    "description": ["description", "narration", "particulars", "details", "merchant"],
    "amount": ["amount", "debit", "credit", "transaction amount"],
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Try to map messy bank CSV columns to our standard schema."""
    mapping = {}
    for std_col, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            if col.strip().lower() in aliases:
                mapping[col] = std_col
                break
    df = df.rename(columns=mapping)
    required = ["date", "description", "amount"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Could not find columns: {missing}. Found: {list(df.columns)}")
    return df[required]

def parse_csv(file_bytes: bytes) -> list[dict]:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df = normalize_columns(df)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    return df.to_dict(orient="records")