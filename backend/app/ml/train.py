"""
Training script — run with: python -m app.ml.train
Generates model/classifier.pkl
"""
import pickle, os
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Labeled training data (expand this — more data = better accuracy)
TRAINING_DATA = [
    # (description, category)
    ("STARBUCKS", "Food & Drink"), ("MCDONALDS", "Food & Drink"),
    ("UBER EATS", "Food & Drink"), ("ZOMATO", "Food & Drink"),
    ("SWIGGY", "Food & Drink"), ("DOMINOS", "Food & Drink"),
    ("AMAZON", "Shopping"), ("FLIPKART", "Shopping"),
    ("MYNTRA", "Shopping"), ("AJIO", "Shopping"),
    ("WALMART", "Groceries"), ("DMART", "Groceries"),
    ("BIGBASKET", "Groceries"), ("BLINKIT", "Groceries"),
    ("UBER", "Transport"), ("OLA", "Transport"),
    ("RAPIDO", "Transport"), ("METRO CARD", "Transport"),
    ("IRCTC", "Transport"), ("MAKEMYTRIP", "Travel"),
    ("AIRTEL", "Utilities"), ("JIO", "Utilities"),
    ("BESCOM", "Utilities"), ("TATA POWER", "Utilities"),
    ("NETFLIX", "Entertainment"), ("SPOTIFY", "Entertainment"),
    ("HOTSTAR", "Entertainment"), ("YOUTUBE PREMIUM", "Entertainment"),
    ("HDFC BANK EMI", "Finance"), ("SBI LOAN", "Finance"),
    ("MUTUAL FUND", "Finance"), ("LIC PREMIUM", "Finance"),
    ("APOLLO PHARMACY", "Health"), ("MEDPLUS", "Health"),
    ("PRACTO", "Health"), ("GYM MEMBERSHIP", "Health"),
    ("SALARY CREDIT", "Income"), ("FREELANCE PAYMENT", "Income"),
    ("DIVIDEND", "Income"), ("CASHBACK", "Income"),
]

descriptions = [d for d, _ in TRAINING_DATA]
labels = [c for _, c in TRAINING_DATA]

X_train, X_test, y_train, y_test = train_test_split(
    descriptions, labels, test_size=0.2, random_state=42
)

# Pipeline: TF-IDF features → Naive Bayes
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),   # unigrams + bigrams
        max_features=5000,
        lowercase=True
    )),
    ("clf", MultinomialNB(alpha=0.1))
])

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred))

os.makedirs("model", exist_ok=True)
with open("model/classifier.pkl", "wb") as f:
    pickle.dump(pipeline, f)
print("Model saved to model/classifier.pkl")