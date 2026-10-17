import hashlib
from collections import Counter

from app.extensions import db
from app.models.db_models import Transaction, MerchantRule, User
from app.ml.classifier import categorize_many


def user_rules(user_id: int) -> dict:
    return {r.merchant_key: r.category for r in MerchantRule.query.filter_by(user_id=user_id)}


def fingerprint(date, description: str, amount: float, tx_type: str, occurrence: int) -> str:
    raw = f"{date.isoformat()}|{' '.join(description.upper().split())}|{amount:.2f}|{tx_type}|{occurrence}"
    return hashlib.sha256(raw.encode()).hexdigest()


def import_rows(user: User, rows: list[dict]) -> dict:
    """Categorise + insert parsed CSV rows, skipping ones already imported.

    Duplicate detection: each row gets a fingerprint of (date, description,
    amount, type, n-th occurrence in this file). Re-uploading the same file
    produces the same fingerprints, but two genuine ₹20 chai payments on the
    same day stay distinct. Lookup is O(1) per row via a set.
    """
    seen_in_file = Counter()
    for r in rows:
        key = (r["date"], r["description"].upper(), r["amount"], r["type"])
        r["fingerprint"] = fingerprint(r["date"], r["description"], r["amount"], r["type"], seen_in_file[key])
        seen_in_file[key] += 1

    lo, hi = min(r["date"] for r in rows), max(r["date"] for r in rows)
    existing = {
        fp for (fp,) in db.session.query(Transaction.fingerprint)
        .filter(Transaction.user_id == user.id, Transaction.date.between(lo, hi),
                Transaction.fingerprint.isnot(None))
    }
    fresh = [r for r in rows if r["fingerprint"] not in existing]

    results = categorize_many(
        [{"description": r["description"], "type": r["type"]} for r in fresh],
        user.profile_type, user_rules(user.id),
    )
    low_confidence = 0
    for r, res in zip(fresh, results):
        if res["source"] == "ml" and res["confidence"] < 0.6:
            low_confidence += 1
        db.session.add(Transaction(
            user_id=user.id, date=r["date"], description=r["description"],
            merchant=res["merchant"] or None, amount=r["amount"], type=r["type"],
            category=res["category"], category_confidence=res["confidence"],
            category_source=res["source"], source="csv", fingerprint=r["fingerprint"],
        ))
    db.session.commit()
    return {
        "imported": len(fresh),
        "duplicates": len(rows) - len(fresh),
        "low_confidence": low_confidence,
    }


def apply_correction(user: User, tx: Transaction, category: str, apply_to_similar: bool) -> int:
    """User fixed a category: remember it as a rule and fix similar rows.
    Returns how many *other* transactions were updated."""
    tx.category = category
    tx.category_source = "manual"
    tx.category_confidence = 1.0
    tx.is_overridden = True
    updated = 0
    if tx.merchant and apply_to_similar:
        rule = MerchantRule.query.filter_by(user_id=user.id, merchant_key=tx.merchant).first()
        if rule:
            rule.category = category
        else:
            db.session.add(MerchantRule(user_id=user.id, merchant_key=tx.merchant, category=category))
        updated = (
            Transaction.query
            .filter(Transaction.user_id == user.id, Transaction.merchant == tx.merchant,
                    Transaction.type == tx.type, Transaction.id != tx.id,
                    Transaction.is_overridden.is_(False))
            .update({"category": category, "category_source": "user_rule",
                     "category_confidence": 1.0}, synchronize_session=False)
        )
    db.session.commit()
    return updated
