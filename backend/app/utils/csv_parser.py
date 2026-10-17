"""
Parses real-world bank statement CSVs.

Handles:
  * junk rows above the header (HDFC/SBI exports start with account details)
  * comma / semicolon / tab separators, UTF-8 BOM and latin-1 files
  * one signed Amount column, separate Debit/Credit columns, or Amount + Dr/Cr column
  * "Rs. 1,234.50", "₹450", "(120.00)", "500 CR" style amounts
  * dd/mm/yyyy, dd-Mon-yy and ISO dates

Returns clean rows: {"date": date, "description": str, "amount": float>0, "type": "income"|"expense"}
Time: O(rows x columns).
"""
import csv
import io
import re

import pandas as pd

MAX_ROWS = 5000

# Priority order matters: "Date" beats "Value Date"
ALIASES = {
    "date": ["date", "txn date", "transaction date", "tran date", "posting date", "value date", "value dt"],
    "description": ["description", "narration", "particulars", "transaction details", "details",
                    "remarks", "transaction remarks", "merchant", "description/narration"],
    "amount": ["amount", "transaction amount", "amount (inr)", "amount(inr)", "amt", "txn amount"],
    "debit": ["debit", "withdrawal", "withdrawal amt", "withdrawal amt.", "withdrawal amount",
              "debit amount", "dr", "debit (inr)", "withdrawals", "paid out"],
    "credit": ["credit", "deposit", "deposit amt", "deposit amt.", "deposit amount",
               "credit amount", "cr", "credit (inr)", "deposits", "paid in"],
    "drcr": ["type", "dr/cr", "cr/dr", "debit/credit", "txn type", "transaction type"],
}
INCOME_HINTS = re.compile(r"\b(SALARY|STIPEND|REFUND|CASHBACK|INTEREST|SCHOLARSHIP|NEFT CR|UPI/CR|CREDIT)\b", re.I)


def _norm(col) -> str:
    return re.sub(r"\s+", " ", str(col).strip().lower())


def _decode(file_bytes: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not read the file. Please upload a CSV exported from your bank.")


def _find_header(text: str) -> tuple[int, str]:
    """Scans the first 40 lines for the row that looks like the table header."""
    try:
        delimiter = csv.Sniffer().sniff(text[:5000], delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    for i, row in enumerate(reader):
        if i >= 40:
            break
        cells = {_norm(c) for c in row}
        has_date = any(c in cells for c in ALIASES["date"])
        has_desc = any(c in cells for c in ALIASES["description"])
        if has_date and has_desc:
            return i, delimiter
    raise ValueError(
        "Couldn't find the header row. Your CSV needs a Date column and a "
        "Description/Narration column."
    )


def _pick(columns: list[str], key: str) -> str | None:
    normalized = {_norm(c): c for c in columns}
    for alias in ALIASES[key]:
        if alias in normalized:
            return normalized[alias]
    return None


def parse_amount(value) -> float | None:
    """'Rs. 1,234.50' -> 1234.5, '(120)' -> -120, '500 DR' -> -500, '' -> None"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return None if pd.isna(value) else float(value)
    s = str(value).strip().upper()
    if not s or s in ("-", "NAN", "NONE"):
        return None
    negative = s.startswith("(") and s.endswith(")") or s.startswith("-") or s.endswith("DR")
    s = re.sub(r"(RS\.?|INR|₹|CR|DR|[,()\s+-])", "", s)
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if negative else v


def parse_csv(file_bytes: bytes) -> dict:
    text = _decode(file_bytes)
    header_idx, delimiter = _find_header(text)
    df = pd.read_csv(
        io.StringIO(text), sep=delimiter, skiprows=header_idx, dtype=str,
        skip_blank_lines=True, on_bad_lines="skip", engine="python",
    )
    cols = list(df.columns)
    date_col = _pick(cols, "date")
    desc_col = _pick(cols, "description")
    amount_col = _pick(cols, "amount")
    debit_col = _pick(cols, "debit")
    credit_col = _pick(cols, "credit")
    drcr_col = _pick(cols, "drcr")

    if not (amount_col or debit_col or credit_col):
        raise ValueError(f"Couldn't find an Amount or Debit/Credit column. Found: {', '.join(map(str, cols))}")
    if len(df) > MAX_ROWS:
        raise ValueError(f"Too many rows ({len(df)}). Max {MAX_ROWS} per upload.")

    dates = pd.to_datetime(df[date_col].str.strip(), dayfirst=True, errors="coerce", format="mixed")

    rows, skipped, all_positive = [], 0, True
    for i in range(len(df)):
        date = dates.iloc[i]
        desc = str(df[desc_col].iloc[i] if pd.notna(df[desc_col].iloc[i]) else "").strip()

        if debit_col or credit_col:
            debit = parse_amount(df[debit_col].iloc[i]) if debit_col else None
            credit = parse_amount(df[credit_col].iloc[i]) if credit_col else None
            signed = (abs(credit) if credit else 0) - (abs(debit) if debit else 0)
            if not debit and not credit and amount_col:
                signed = parse_amount(df[amount_col].iloc[i]) or 0
            all_positive = False
        else:
            signed = parse_amount(df[amount_col].iloc[i])
            if signed is None:
                signed = 0
            if drcr_col:
                flag = str(df[drcr_col].iloc[i]).strip().upper()
                if flag.startswith("D"):
                    signed = -abs(signed)
                elif flag.startswith("C"):
                    signed = abs(signed)
                all_positive = False
            elif signed < 0:
                all_positive = False

        if pd.isna(date) or not desc or not signed:
            skipped += 1
            continue
        rows.append({"date": date.date(), "description": desc[:255], "signed": signed})

    if not rows:
        raise ValueError("No valid transactions found in this file.")

    warnings = []
    if all_positive:
        # No sign info at all: assume spends, except obvious incoming money
        warnings.append("No debit/credit info found, so amounts were treated as expenses "
                        "unless the description looked like income.")
        for r in rows:
            if not INCOME_HINTS.search(r["description"]):
                r["signed"] = -abs(r["signed"])

    out = [{
        "date": r["date"],
        "description": r["description"],
        "amount": round(abs(r["signed"]), 2),
        "type": "income" if r["signed"] > 0 else "expense",
    } for r in rows]
    return {"rows": out, "skipped": skipped, "warnings": warnings}
