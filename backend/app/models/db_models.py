from datetime import datetime, timezone
from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(60), nullable=False, default="")

    role = db.Column(db.String(20), nullable=False, default="user")      # user | admin | demo
    profile_type = db.Column(db.String(20))                              # student | employee | freelancer
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    onboarded = db.Column(db.Boolean, nullable=False, default=False)

    # Onboarding answers (student: allowance, employee: salary, freelancer: avg income)
    monthly_income = db.Column(db.Float, nullable=False, default=0)
    income_day = db.Column(db.Integer, nullable=False, default=1)        # day of month money arrives
    living = db.Column(db.String(20))                                    # hostel | pg | day_scholar | home
    tax_rate = db.Column(db.Float, nullable=False, default=0.10)         # freelancer tax set-aside

    created_at = db.Column(db.DateTime, default=utcnow)
    last_login_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "profile_type": self.profile_type,
            "is_active": self.is_active,
            "onboarded": self.onboarded,
            "monthly_income": self.monthly_income,
            "income_day": self.income_day,
            "living": self.living,
            "tax_rate": self.tax_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (
        db.UniqueConstraint("user_id", "fingerprint", name="uq_user_fingerprint"),
        db.Index("ix_tx_user_date", "user_id", "date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    merchant = db.Column(db.String(120))                   # cleaned merchant key, e.g. "SWIGGY"
    amount = db.Column(db.Float, nullable=False)           # always positive
    type = db.Column(db.String(10), nullable=False)        # income | expense
    category = db.Column(db.String(100))
    category_confidence = db.Column(db.Float)
    category_source = db.Column(db.String(10))             # rule | user_rule | ml | manual
    source = db.Column(db.String(10), default="csv")       # csv | manual
    is_overridden = db.Column(db.Boolean, default=False)   # user corrected the category
    note = db.Column(db.String(255))
    fingerprint = db.Column(db.String(64))                 # sha256 for duplicate detection
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "description": self.description,
            "merchant": self.merchant,
            "amount": round(self.amount, 2),
            "type": self.type,
            "category": self.category,
            "confidence": self.category_confidence,
            "category_source": self.category_source,
            "source": self.source,
            "is_overridden": self.is_overridden,
            "note": self.note,
        }


class Budget(db.Model):
    __tablename__ = "budgets"
    __table_args__ = (db.UniqueConstraint("user_id", "category", name="uq_user_budget"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    saved_amount = db.Column(db.Float, nullable=False, default=0)
    deadline = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": self.target_amount,
            "saved_amount": self.saved_amount,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "progress": round(min(self.saved_amount / self.target_amount, 1) * 100, 1)
            if self.target_amount else 0,
        }


class MerchantRule(db.Model):
    """When a user re-categorises SWIGGY as 'Fun', future SWIGGY rows follow."""
    __tablename__ = "merchant_rules"
    __table_args__ = (db.UniqueConstraint("user_id", "merchant_key", name="uq_user_rule"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_key = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)


class Insight(db.Model):
    __tablename__ = "insights"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(20), default="rules")      # groq | gemini | rules
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "content": self.content,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ModelRun(db.Model):
    """Every (re)training of the classifier, so admin can see metrics over time."""
    __tablename__ = "model_runs"

    id = db.Column(db.Integer, primary_key=True)
    accuracy = db.Column(db.Float)
    macro_f1 = db.Column(db.Float)
    n_samples = db.Column(db.Integer)
    n_user_corrections = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "accuracy": self.accuracy,
            "macro_f1": self.macro_f1,
            "n_samples": self.n_samples,
            "n_user_corrections": self.n_user_corrections,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
