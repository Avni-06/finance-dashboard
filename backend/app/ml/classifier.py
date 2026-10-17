"""
Hybrid categoriser, in priority order:

  1. user rule   - the user corrected this merchant before        (confidence 1.0)
  2. brand rule  - a known brand keyword is in the narration      (confidence 0.95)
  3. ML model    - TF-IDF + Logistic Regression, masked by type   (model probability)
  4. fallback    - "Other" / "Other Income" when the model is unsure

The model predicts a profile-independent concept which is then mapped to the
user's own categories (student / employee / freelancer).

Complexity: one regex pass per row for rules (O(len)), and a single
vectorised predict_proba call for all rows that need ML.
"""
import json
import os
import re
import threading

import joblib
import numpy as np

from app.ml.concepts import (
    KEYWORDS, CONCEPT_TO_CATEGORY, INCOME_CONCEPTS, EXPENSE_CONCEPTS, concept_type,
)
from app.ml.train import MODEL_PATH, METRICS_PATH, train
from app.utils.merchant import clean_text, merchant_key

LOW_CONFIDENCE = 0.35

_model = None
_lock = threading.Lock()

# One big alternation regex, longest keywords first so "SWIGGY INSTAMART"
# beats "SWIGGY" and "AMAZON PRIME" beats "AMAZON".
_KW_TO_CONCEPT = {}
for _concept, _words in KEYWORDS.items():
    for _w in _words:
        _KW_TO_CONCEPT.setdefault(clean_text(_w), _concept)
_KW_RE = re.compile(
    r"(?<![A-Z&])(" + "|".join(re.escape(k) for k in sorted(_KW_TO_CONCEPT, key=len, reverse=True)) + r")(?![A-Z&])"
)


def get_model():
    """Loads the model, training it first if the file is missing (fresh clone/deploy)."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                if os.path.exists(MODEL_PATH):
                    _model = joblib.load(MODEL_PATH)
                else:
                    _model = train()["model"]
    return _model


def set_model(model):
    global _model
    _model = model


def model_metrics() -> dict | None:
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH) as f:
            return json.load(f)
    return None


def rule_concept(cleaned: str, tx_type: str) -> str | None:
    """Longest brand keyword whose concept matches the transaction type."""
    best = None
    for m in _KW_RE.finditer(cleaned):
        concept = _KW_TO_CONCEPT[m.group(1)]
        if concept_type(concept) != tx_type:
            continue
        if best is None or len(m.group(1)) > len(best[0]):
            best = (m.group(1), concept)
    return best[1] if best else None


def _fallback(tx_type: str) -> str:
    return "Other Income" if tx_type == "income" else "Other"


def categorize_many(items: list[dict], profile_type: str, user_rules: dict | None = None) -> list[dict]:
    """items: [{"description": str, "type": "income"|"expense"}, ...]
    Returns one dict per item: category, concept, confidence, source, merchant."""
    profile_type = profile_type or "student"
    mapping = CONCEPT_TO_CATEGORY[profile_type]
    user_rules = user_rules or {}
    results: list[dict | None] = [None] * len(items)
    need_ml = []

    for i, item in enumerate(items):
        cleaned = clean_text(item["description"])
        merchant = merchant_key(item["description"])
        tx_type = item["type"]

        if merchant and merchant in user_rules:
            results[i] = {"category": user_rules[merchant], "concept": None,
                          "confidence": 1.0, "source": "user_rule", "merchant": merchant}
            continue
        concept = rule_concept(cleaned, tx_type)
        if concept:
            results[i] = {"category": mapping[concept], "concept": concept,
                          "confidence": 0.95, "source": "rule", "merchant": merchant}
            continue
        need_ml.append((i, cleaned, merchant, tx_type))

    if need_ml:
        model = get_model()
        classes = list(model.classes_)
        income_mask = np.array([c in INCOME_CONCEPTS for c in classes])
        expense_mask = np.array([c in EXPENSE_CONCEPTS for c in classes])
        probas = model.predict_proba([row[1] or "UNKNOWN" for row in need_ml])

        for (i, _cleaned, merchant, tx_type), proba in zip(need_ml, probas):
            mask = income_mask if tx_type == "income" else expense_mask
            p = np.where(mask, proba, 0)
            total = p.sum()
            p = p / total if total > 0 else p
            best = int(p.argmax())
            confidence = float(p[best])
            concept = classes[best]
            if confidence < LOW_CONFIDENCE:
                category = _fallback(tx_type)
            else:
                category = mapping[concept]
            results[i] = {"category": category, "concept": concept,
                          "confidence": round(confidence, 3), "source": "ml", "merchant": merchant}
    return results


def categorize(description: str, tx_type: str, profile_type: str, user_rules: dict | None = None) -> dict:
    return categorize_many([{"description": description, "type": tx_type}], profile_type, user_rules)[0]
