import pickle
import os
import re

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../model/classifier.pkl")

_pipeline = None

def load_model():
    global _pipeline
    if _pipeline is None:
        with open(MODEL_PATH, "rb") as f:
            _pipeline = pickle.load(f)
    return _pipeline

def preprocess(text: str) -> str:
    """Clean a transaction description before classification."""
    text = text.upper()
    text = re.sub(r"\d{4,}", "", text)   # remove long numbers (card/ref numbers)
    text = re.sub(r"[^A-Z\s]", " ", text)
    return text.strip()

def classify_transaction(description: str) -> dict:
    """Returns category and confidence score."""
    model = load_model()
    cleaned = preprocess(description)
    category = model.predict([cleaned])[0]
    proba = model.predict_proba([cleaned])[0]
    confidence = float(max(proba))
    return {"category": category, "confidence": round(confidence, 3)}