"""
Turns messy bank narrations into a clean, comparable merchant key.

  "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment"  -> "SWIGGY"
  "POS 4123XXXXXXXX1234 AMAZON PAY IN BANGALORE"          -> "AMAZON PAY"
  "NEFT CR-HDFC0000123-ACME TECH PVT LTD-SALARY OCT"      -> "ACME TECH SALARY"

Time: O(n) in the length of the narration.
"""
import re

# Words that describe the payment rail, not the merchant
NOISE = {
    "UPI", "DR", "CR", "POS", "NEFT", "IMPS", "RTGS", "ACH", "NACH", "ECS", "P2P", "P2M", "P2A",
    "MB", "IB", "BIL", "BILLPAY", "ONL", "ECOM", "PUR", "PURCHASE", "TXN", "TRF", "TRANSFER",
    "REF", "NO", "PAYMENT", "PAYMENTS", "PAY", "TO", "FROM", "VIA", "BY", "FOR", "THE", "AND",
    "INR", "RS", "DEBIT", "CREDIT", "CARD", "VISA", "MASTERCARD", "RUPAY", "COLLECT", "REQUEST",
    "SENT", "RECEIVED", "PVT", "LTD", "LIMITED", "PRIVATE", "INDIA", "IN", "LLP", "INC",
    "DEBITED", "CREDITED", "AC", "A", "C", "OF", "ON", "AT", "WITH", "ID", "MOB", "MOBILE",
}
# Bank / PSP handles that show up in UPI strings
BANK_CODES = {
    "YESB", "HDFC", "ICIC", "SBIN", "UTIB", "KKBK", "PUNB", "BARB", "CNRB", "IDIB", "INDB",
    "PYTM", "PAYTM", "YBL", "OKAXIS", "OKHDFCBANK", "OKICICI", "OKSBI", "AXL", "IBL", "APL",
    "HDFCBANK", "ICICI", "AXIS", "SBI", "KOTAK", "AIRP", "FBL", "RATN", "AUBL",
}
# Common city names that trail POS narrations
CITIES = {
    "DELHI", "NEW", "MUMBAI", "BANGALORE", "BENGALURU", "PUNE", "HYDERABAD", "CHENNAI",
    "KOLKATA", "NOIDA", "GURGAON", "GURUGRAM", "JAIPUR", "LUCKNOW", "AHMEDABAD", "IN",
}
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
MASKED_CARD_RE = re.compile(r"^[0-9X*]{6,}$")


def clean_text(text: str) -> str:
    """Uppercase, split VPAs into their handle, drop numbers and symbols."""
    t = str(text or "").upper()
    t = re.sub(r"([A-Z0-9._-]+)@[A-Z0-9.]+", r" \1 ", t)     # swiggy@ybl -> swiggy
    t = re.sub(r"[/|\\\-_:;,#*()\[\]]+", " ", t)
    t = re.sub(r"\.", " ", t)
    tokens = []
    for tok in t.split():
        if IFSC_RE.match(tok) or MASKED_CARD_RE.match(tok):
            continue
        if sum(ch.isdigit() for ch in tok) >= 3:              # refs, phone numbers, dates
            continue
        tok = re.sub(r"[^A-Z&]", "", tok)
        if tok:
            tokens.append(tok)
    return " ".join(tokens)


def merchant_key(text: str) -> str:
    """Best-guess merchant name, max 3 words. Empty string if nothing useful."""
    words = [
        w for w in clean_text(text).split()
        if w not in NOISE and w not in BANK_CODES and w not in CITIES and len(w) > 1
    ]
    # De-duplicate while preserving order. Also drops VPA handles that just
    # repeat the name: "GUPTA MEDICOS GUPTAMED" -> "GUPTA MEDICOS".
    uniq = []
    for w in words:
        joined = "".join(uniq)
        if w in uniq or (uniq and len(w) >= 4 and (joined.startswith(w) or w.startswith(uniq[0]))):
            continue
        uniq.append(w)
    return " ".join(uniq[:3])[:120]
