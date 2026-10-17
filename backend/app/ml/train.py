"""
Train the transaction classifier.

  python -m app.ml.train

Pipeline: cleaned narration -> TF-IDF (word 1-2 grams + char 3-5 grams)
          -> multinomial Logistic Regression over ~27 concepts.

Evaluation uses a *group split by merchant*: test merchants never appear in
training, so the score reflects real generalisation, not memorisation.
"""
import json
import os
from datetime import datetime, timezone

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline, FeatureUnion

from app.ml.dataset import build_dataset
from app.utils.merchant import clean_text

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "model"))
MODEL_PATH = os.path.join(MODEL_DIR, "classifier.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")
CORRECTION_WEIGHT = 3  # a real user correction counts 3x a synthetic row


def make_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), lowercase=False,
                                 token_pattern=r"[A-Z&]{2,}", sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=False,
                                 min_df=2, sublinear_tf=True)),
    ])
    return Pipeline([
        ("features", features),
        ("clf", LogisticRegression(C=8, max_iter=3000)),
    ])


def train(corrections: list[tuple[str, str]] | None = None, save: bool = True) -> dict:
    """corrections: [(raw_description, concept), ...] from users' category overrides."""
    corrections = corrections or []
    rows = build_dataset()
    X = [clean_text(narration) for _, narration, _ in rows]
    y = [concept for _, _, concept in rows]
    groups = [merchant for merchant, _, _ in rows]

    # 1) Honest evaluation on unseen merchants
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(split.split(X, y, groups))
    eval_model = make_pipeline()
    eval_model.fit([X[i] for i in train_idx], [y[i] for i in train_idx])
    y_true = [y[i] for i in test_idx]
    y_pred = eval_model.predict([X[i] for i in test_idx])
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    metrics = {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "macro_f1": round(f1_score(y_true, y_pred, average="macro"), 4),
        "n_samples": len(X) + len(corrections) * CORRECTION_WEIGHT,
        "n_test": len(test_idx),
        "n_user_corrections": len(corrections),
        "per_concept_f1": {
            k: round(v["f1-score"], 3) for k, v in report.items()
            if isinstance(v, dict) and k not in ("macro avg", "weighted avg")
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    # 2) Final model on everything + user corrections
    X_all = X + [clean_text(d) for d, _ in corrections] * CORRECTION_WEIGHT
    y_all = y + [c for _, c in corrections] * CORRECTION_WEIGHT
    model = make_pipeline()
    model.fit(X_all, y_all)

    if save:
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        with open(METRICS_PATH, "w") as f:
            json.dump(metrics, f, indent=2)
    return {"model": model, "metrics": metrics}


if __name__ == "__main__":
    result = train()
    m = result["metrics"]
    print(f"Accuracy on unseen merchants: {m['accuracy']:.2%}  |  macro-F1: {m['macro_f1']:.3f}")
    print(f"Samples: {m['n_samples']}  ->  saved to {MODEL_PATH}")
