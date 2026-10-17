"""
Demo accounts with ~6 months of realistic, bank-style transactions.

Data is generated relative to *today*, so the demo always looks current.
Raw narrations go through the real categoriser, so the demo also shows
the classifier at work. If the data is more than 3 days old it is rebuilt.
"""
import random
import secrets
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.db_models import User, Transaction, Budget, Goal, MerchantRule, Insight
from app.constants import BUDGET_TEMPLATES
from app.ml.classifier import categorize_many
from app.services.analytics import shift_month

DEMO_ACCOUNTS = {
    "student": {"email": "demo.student@finsight.app", "name": "Aanya (Demo)",
                "monthly_income": 9000, "income_day": 1, "living": "hostel"},
    "employee": {"email": "demo.employee@finsight.app", "name": "Rohan (Demo)",
                 "monthly_income": 72000, "income_day": 1, "living": None},
    "freelancer": {"email": "demo.freelancer@finsight.app", "name": "Meera (Demo)",
                   "monthly_income": 60000, "income_day": 1, "living": None},
}
MONTHS = 6


def _upi(rng, name, handle=None, credit=False):
    ref = rng.randint(10**11, 10**12 - 1)
    handle = handle or name.lower().replace(" ", "")[:10]
    psp = rng.choice(["ybl", "okaxis", "paytm", "okhdfcbank"])
    bank = rng.choice(["YESB", "HDFC", "ICIC", "SBIN", "UTIB"])
    return f"UPI/{'CR' if credit else 'DR'}/{ref}/{name}/{bank}/{handle}@{psp}/Payment"


def _days(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _student_rows(rng: random.Random, start: date, today: date) -> list[tuple]:
    rows = []  # (date, description, amount, type)
    friends = ["RIYA SINGH", "KAVYA NAIR", "ISHA MEHTA", "TANYA GUPTA"]
    current_month = (today.year, today.month)
    for d in _days(start, today):
        this_month = (d.year, d.month) == current_month
        if d.day == 1:
            rows.append((d, _upi(rng, "PAPA", "papa.sharma", credit=True), 9000, "income"))
        if d.day == 12:
            rows.append((d, "SPOTIFY INDIA STUDENT", 59, "expense"))
        if d.day == 20:
            rows.append((d, "BIL/ONL/" + str(rng.randint(10**9, 10**10)) + "/AIRTEL PREPAID RECHARGE", 299, "expense"))
        # Canteen / mess most weekdays
        if d.weekday() < 5 and rng.random() < 0.7:
            rows.append((d, _upi(rng, "IGDTU CANTEEN", "igdtucanteen"), rng.choice([30, 40, 50, 60, 80, 90, 120]), "expense"))
        # Food delivery: more often this month (shows the anomaly alert)
        if rng.random() < (0.35 if this_month else 0.12):
            rows.append((d, _upi(rng, rng.choice(["SWIGGY", "ZOMATO"])), rng.randint(180, 450), "expense"))
        if rng.random() < 0.06:
            rows.append((d, _upi(rng, rng.choice(["BLINKIT", "ZEPTO"])), rng.randint(120, 380), "expense"))
        if rng.random() < 0.18:
            rows.append((d, _upi(rng, rng.choice(["DMRC", "RAPIDO", "UBER INDIA"]), "travel"),
                         rng.choice([30, 40, 50, 70, 120, 160, 220]), "expense"))
        if rng.random() < 0.05:
            rows.append((d, _upi(rng, rng.choice(["SHARMA XEROX", "MODERN STATIONERS"])), rng.randint(20, 150), "expense"))
        if rng.random() < 0.035:
            rows.append((d, "POS 4591XXXXXXXX2231 " + rng.choice(["AMAZON PAY IN", "MYNTRA DESIGNS", "FLIPKART INTERNET"]),
                         rng.randint(299, 1499), "expense"))
        if rng.random() < 0.03:
            rows.append((d, _upi(rng, rng.choice(["BOOKMYSHOW", "PVR CINEMAS"])), rng.randint(220, 450), "expense"))
        if rng.random() < 0.05:
            rows.append((d, _upi(rng, rng.choice(friends)), rng.choice([100, 150, 200, 250, 350]), "expense"))
        if rng.random() < 0.015:
            rows.append((d, _upi(rng, "GUPTA MEDICOS", "guptamed"), rng.randint(80, 320), "expense"))
    # One-offs
    sem = start + timedelta(days=20)
    rows.append((sem, "NEFT CR-SBIN0001234-PAPA SHARMA-SEMESTER FEES", 52000, "income"))
    rows.append((sem + timedelta(days=2), "BIL/ONL/9988776655/IGDTU SEMESTER FEE", 52000, "expense"))
    rows.append((sem + timedelta(days=6), _upi(rng, "VERMA BOOK DEPOT", "vermabooks"), 1350, "expense"))
    rows.append((start + timedelta(days=70), "NSP SCHOLARSHIP CREDIT", 12000, "income"))
    rows.append((start + timedelta(days=95), _upi(rng, "DEVFOLIO", "devfolio"), 299, "expense"))
    rows.append((start + timedelta(days=96), "MAKEMYTRIP INDIA PVT LTD", 1840, "expense"))
    rows.append((start + timedelta(days=130), "UDEMY ONLINE COURSES", 449, "expense"))
    for i in (2, 1):  # internship stipend for the last two months
        y, m = shift_month(today.year, today.month, -i)
        rows.append((date(y, m, 10), "NEFT CR-HDFC0000999-NOVA LABS-INTERNSHIP STIPEND", 10000, "income"))
    return rows


def _employee_rows(rng: random.Random, start: date, today: date) -> list[tuple]:
    rows = []
    bonus_given = False
    for d in _days(start, today):
        if d.day == 1:
            rows.append((d, "NEFT CR-CITI0000001-ACME TECHNOLOGIES PVT LTD-SALARY", 72000, "income"))
        if d.day == 3:
            rows.append((d, "NOBROKER RENT PAYMENT FLAT 402", 20000, "expense"))
        if d.day == 5:
            rows.append((d, "ACH D- BAJAJ FINANCE LTD EMI-" + str(rng.randint(10**7, 10**8)), 4200, "expense"))
        if d.day == 7:
            rows.append((d, "ACH D- GROWW MUTUAL FUND SIP", 10000, "expense"))
        if d.day == 10:
            rows.append((d, "BIL/ONL/" + str(rng.randint(10**9, 10**10)) + "/BSES RAJDHANI POWER", rng.randint(1100, 2200), "expense"))
        if d.day == 15:
            rows.append((d, "NETFLIX.COM", 649, "expense"))
        if d.day == 18:
            rows.append((d, "AIRTEL POSTPAID BILL", 599, "expense"))
        if d.day == 2:
            rows.append((d, "CULTFIT MEMBERSHIP", 1499, "expense"))
        if d.weekday() == 6 or rng.random() < 0.05:
            rows.append((d, _upi(rng, rng.choice(["BIGBASKET", "BLINKIT", "DMART"])), rng.randint(450, 1900), "expense"))
        if rng.random() < 0.28:
            rows.append((d, _upi(rng, rng.choice(["SWIGGY", "ZOMATO", "STARBUCKS", "CHAAYOS"])), rng.randint(180, 750), "expense"))
        if d.weekday() < 5 and rng.random() < 0.35:
            rows.append((d, _upi(rng, rng.choice(["UBER INDIA", "OLA CABS", "RAPIDO"])), rng.randint(140, 480), "expense"))
        if rng.random() < 0.05:
            rows.append((d, "POS 5241XXXXXXXX8812 " + rng.choice(["AMAZON PAY IN", "MYNTRA DESIGNS", "CROMA RETAIL", "DECATHLON"]),
                         rng.randint(800, 4500), "expense"))
        if rng.random() < 0.03:
            rows.append((d, _upi(rng, rng.choice(["PVR CINEMAS", "BOOKMYSHOW"])), rng.randint(400, 1200), "expense"))
        if rng.random() < 0.04:
            rows.append((d, "IOCL PETROL PUMP " + rng.choice(["DELHI", "NOIDA"]), rng.randint(500, 1500), "expense"))
        if not bonus_given and d >= start + timedelta(days=100):
            rows.append((d, "NEFT CR-CITI0000001-ACME TECHNOLOGIES-PERFORMANCE BONUS", 25000, "income"))
            bonus_given = True
    rows.append((start + timedelta(days=40), "INDIGO AIRLINES", 6400, "expense"))
    rows.append((start + timedelta(days=41), "OYO ROOMS GOA", 5200, "expense"))
    return rows


def _freelancer_rows(rng: random.Random, start: date, today: date) -> list[tuple]:
    rows = []
    clients = ["UPWORK ESCROW INC", "PIXEL STUDIOS INVOICE", "BRIGHTLEAF DIGITAL CLIENT", "NORTHSTAR CONSULTING PAYMENT"]
    for d in _days(start, today):
        if d.day == 6 or rng.random() < 0.05:
            rows.append((d, "NEFT CR-HDFC0000456-" + rng.choice(clients), rng.choice([12000, 18000, 25000, 32000, 45000]), "income"))
        if d.day == 4:
            rows.append((d, "HOUSING RENT TRANSFER", 16000, "expense"))
        if d.day == 8:
            rows.append((d, "FIGMA MONTHLY", 1250, "expense"))
            rows.append((d, "GITHUB INC", 340, "expense"))
        if d.day == 12:
            rows.append((d, "AMAZON WEB SERVICES", rng.randint(700, 2600), "expense"))
        if d.day == 20:
            rows.append((d, "ACT FIBERNET BROADBAND", 999, "expense"))
        if d.day == 15 and d.month in (6, 9, 12, 3):
            rows.append((d, "CBDT ADVANCE TAX PAYMENT", rng.choice([15000, 20000]), "expense"))
        if rng.random() < 0.22:
            rows.append((d, _upi(rng, rng.choice(["SWIGGY", "ZOMATO", "BLUE TOKAI", "THIRD WAVE COFFEE"])), rng.randint(180, 650), "expense"))
        if rng.random() < 0.07:
            rows.append((d, _upi(rng, rng.choice(["BLINKIT", "ZEPTO"])), rng.randint(300, 1200), "expense"))
        if rng.random() < 0.12:
            rows.append((d, _upi(rng, rng.choice(["UBER INDIA", "RAPIDO"])), rng.randint(90, 420), "expense"))
        if rng.random() < 0.02:
            rows.append((d, "KONFHUB DESIGN CONFERENCE", 2500, "expense"))
    return rows


GENERATORS = {"student": _student_rows, "employee": _employee_rows, "freelancer": _freelancer_rows}


def _goals(profile_type: str, today: date) -> list[Goal]:
    if profile_type == "student":
        return [
            Goal(name="New laptop", target_amount=60000, saved_amount=18500, deadline=today + timedelta(days=150)),
            Goal(name="Goa trip with friends", target_amount=12000, saved_amount=4200, deadline=today + timedelta(days=75)),
            Goal(name="Hackathon travel fund", target_amount=3000, saved_amount=3000),
        ]
    if profile_type == "employee":
        return [
            Goal(name="Emergency fund", target_amount=300000, saved_amount=145000),
            Goal(name="Japan trip", target_amount=180000, saved_amount=52000, deadline=today + timedelta(days=240)),
        ]
    return [
        Goal(name="Tax reserve", target_amount=80000, saved_amount=46000, deadline=today + timedelta(days=120)),
        Goal(name="New camera", target_amount=95000, saved_amount=21000),
    ]


def seed_demo_user(profile_type: str, today: date | None = None) -> User:
    today = today or date.today()
    cfg = DEMO_ACCOUNTS[profile_type]
    user = User.query.filter_by(email=cfg["email"]).first()
    if not user:
        user = User(email=cfg["email"], role="demo",
                    password_hash=generate_password_hash(secrets.token_hex(16)))
        db.session.add(user)
    user.name, user.profile_type, user.onboarded = cfg["name"], profile_type, True
    user.monthly_income, user.income_day, user.living = cfg["monthly_income"], cfg["income_day"], cfg["living"]
    user.is_active, user.role = True, "demo"
    db.session.flush()

    for model in (Transaction, Budget, Goal, MerchantRule, Insight):
        model.query.filter_by(user_id=user.id).delete()

    y, m = shift_month(today.year, today.month, -(MONTHS - 1))
    start = date(y, m, 1)
    rng = random.Random(f"{profile_type}-{today.isoformat()}")
    rows = sorted(GENERATORS[profile_type](rng, start, today), key=lambda r: r[0])
    rows = [r for r in rows if start <= r[0] <= today]

    results = categorize_many([{"description": r[1], "type": r[3]} for r in rows], profile_type)
    for (d, desc, amount, tx_type), res in zip(rows, results):
        db.session.add(Transaction(
            user_id=user.id, date=d, description=desc, amount=float(amount), type=tx_type,
            merchant=res["merchant"] or None, category=res["category"],
            category_confidence=res["confidence"], category_source=res["source"], source="csv",
        ))
    for category, share in BUDGET_TEMPLATES[profile_type].items():
        db.session.add(Budget(user_id=user.id, category=category,
                              monthly_limit=round(cfg["monthly_income"] * share / 50) * 50))
    for g in _goals(profile_type, today):
        g.user_id = user.id
        db.session.add(g)
    db.session.commit()
    return user


def ensure_demo_user(profile_type: str) -> User:
    """Returns the demo user, rebuilding its data if missing or stale."""
    cfg = DEMO_ACCOUNTS[profile_type]
    user = User.query.filter_by(email=cfg["email"]).first()
    if user:
        latest = (Transaction.query.filter_by(user_id=user.id)
                  .order_by(Transaction.date.desc()).first())
        if latest and (date.today() - latest.date).days <= 3 and latest.date <= date.today():
            return user
    return seed_demo_user(profile_type)
