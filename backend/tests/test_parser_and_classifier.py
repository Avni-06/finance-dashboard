from datetime import date

import pytest

from app.ml.classifier import categorize
from app.utils.csv_parser import parse_csv, parse_amount
from app.utils.merchant import merchant_key

HDFC_STYLE = b"""HDFC BANK Ltd.
Account No : 50100XXXXXX

Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance
01/09/26,UPI-SWIGGY-swiggy@ybl-YESB0000001-424242424242-UPI,424242424242,01/09/26,"1,250.00",,"10,000.00"
02/09/26,NEFT CR-HDFC0000123-ACME TECH-STIPEND SEP,N1234,02/09/26,,"15,000.00","25,000.00"
"""


@pytest.mark.parametrize("raw,expected", [
    ("Rs. 1,234.50", 1234.5), ("₹450", 450), ("(120.00)", -120), ("500 DR", -500),
    ("-20", -20), ("", None), ("abc", None),
])
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected


def test_parses_bank_export_with_junk_header_and_debit_credit():
    out = parse_csv(HDFC_STYLE)
    rows = out["rows"]
    assert len(rows) == 2
    assert rows[0] == {"date": date(2026, 9, 1), "description": rows[0]["description"],
                       "amount": 1250.0, "type": "expense"}
    assert rows[1]["type"] == "income" and rows[1]["amount"] == 15000


def test_parses_signed_amount_and_drcr_flag():
    signed = parse_csv(b"Date,Description,Amount\n2024-01-15,Swiggy,-450\n2024-01-16,Salary Credit,50000\n")["rows"]
    assert [r["type"] for r in signed] == ["expense", "income"]
    flagged = parse_csv("Txn Date;Particulars;Amount;Dr/Cr\n15-Sep-2026;BLINKIT;₹320;DR\n".encode())["rows"]
    assert flagged[0]["type"] == "expense" and flagged[0]["amount"] == 320


def test_rejects_csv_without_required_columns():
    with pytest.raises(ValueError):
        parse_csv(b"foo,bar\n1,2\n")


@pytest.mark.parametrize("narration,expected", [
    ("UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment", "SWIGGY"),
    ("UPI-GUPTA MEDICOS-guptamed@okaxis-SBIN0001234-123456789012-UPI", "GUPTA MEDICOS"),
    ("POS 4123XXXXXXXX1234 AMAZON PAY IN BANGALORE", "AMAZON"),
])
def test_merchant_key(narration, expected):
    assert merchant_key(narration) == expected


def test_brand_rule_and_profile_mapping():
    s = categorize("UPI/DR/1/SWIGGY/YESB/swiggy@ybl", "expense", "student")
    e = categorize("UPI/DR/1/SWIGGY/YESB/swiggy@ybl", "expense", "employee")
    assert s["category"] == "Food & Canteen" and e["category"] == "Food & Dining"
    assert s["source"] == "rule"


def test_longest_keyword_wins():
    assert categorize("AMAZON PRIME VIDEO", "expense", "student")["category"] == "Subscriptions"
    assert categorize("UBER EATS ORDER", "expense", "employee")["category"] == "Food & Dining"


def test_ml_generalises_to_unseen_merchant():
    r = categorize("KHANNA DHABA DELHI", "expense", "student")
    assert r["source"] == "ml" and r["category"] == "Food & Canteen"


def test_type_masking_keeps_income_as_income():
    r = categorize("REFUND SWIGGY ORDER", "income", "student")
    assert r["category"] in ("Other Income", "Allowance", "Stipend", "Scholarship", "Part-time")


def test_user_rule_beats_everything_and_matches_prefix():
    rules = {"SWIGGY": "Fun"}
    assert categorize("SWIGGY late night", "expense", "student", rules)["category"] == "Fun"
    # rule category is an expense category, so it must not apply to income rows
    assert categorize("SWIGGY refund", "income", "student", rules)["category"] != "Fun"
