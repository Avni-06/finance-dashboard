import re
from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.db_models import User, Budget, utcnow
from app.constants import PROFILE_TYPES, LIVING_TYPES, BUDGET_TEMPLATES
from app.utils.errors import ApiError
from app.utils.security import current_user, login_required, writable
from app.utils.validation import json_body, as_float, as_int, as_str

auth_bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def auth_response(user: User, status: int = 200):
    user.last_login_at = utcnow()
    db.session.commit()
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"token": token, "user": user.to_dict()}), status


def _validate_password(pw: str):
    if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        raise ApiError("Password needs 8+ characters with at least one letter and one number")


@auth_bp.post("/register")
def register():
    data = json_body()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    name = as_str(data.get("name"), "Name", 2, 60)
    profile_type = data.get("profile_type") or "student"

    if not EMAIL_RE.match(email) or len(email) > 120:
        raise ApiError("Enter a valid email")
    _validate_password(password)
    if profile_type not in PROFILE_TYPES:
        raise ApiError(f"profile_type must be one of: {', '.join(PROFILE_TYPES)}")
    if User.query.filter_by(email=email).first():
        raise ApiError("This email is already registered", 409)

    # Role is never taken from the client. Admins are created via manage.py only.
    user = User(
        email=email,
        name=name,
        password_hash=generate_password_hash(password),
        role="user",
        profile_type=profile_type,
    )
    db.session.add(user)
    db.session.commit()
    return auth_response(user, 201)


@auth_bp.post("/login")
def login():
    data = json_body()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        raise ApiError("Wrong email or password", 401)
    if not user.is_active:
        raise ApiError("This account has been deactivated", 403)
    return auth_response(user)


@auth_bp.get("/me")
@login_required
def me():
    return jsonify({"user": current_user().to_dict()})


@auth_bp.patch("/profile")
@writable
def update_profile():
    """Used by onboarding (first time) and the Settings page."""
    user = current_user()
    data = json_body()
    first_time = not user.onboarded

    profile_type = data.get("profile_type", user.profile_type)
    if profile_type not in PROFILE_TYPES:
        raise ApiError("Invalid profile_type")

    if "name" in data:
        user.name = as_str(data["name"], "Name", 2, 60)
    if "monthly_income" in data:
        user.monthly_income = as_float(data["monthly_income"], "Monthly income")
    if "income_day" in data:
        user.income_day = as_int(data["income_day"], "Income day", 1, 31)
    if "tax_rate" in data:
        user.tax_rate = as_float(data["tax_rate"], "Tax rate", 0, 0.5)

    living = data.get("living", user.living)
    if profile_type == "student":
        if living not in LIVING_TYPES:
            raise ApiError(f"living must be one of: {', '.join(LIVING_TYPES)}")
        user.living = living
    else:
        user.living = None

    user.profile_type = profile_type
    user.onboarded = True

    # First-time onboarding: create a sensible starter budget from the template
    if first_time and user.monthly_income > 0 and not Budget.query.filter_by(user_id=user.id).count():
        for category, share in BUDGET_TEMPLATES[profile_type].items():
            db.session.add(Budget(
                user_id=user.id, category=category,
                monthly_limit=round(user.monthly_income * share / 50) * 50 or 50,
            ))

    db.session.commit()
    return jsonify({"user": user.to_dict()})


@auth_bp.patch("/password")
@writable
def change_password():
    user = current_user()
    data = json_body()
    if not check_password_hash(user.password_hash, str(data.get("current_password", ""))):
        raise ApiError("Current password is wrong", 400)
    new = str(data.get("new_password", ""))
    _validate_password(new)
    user.password_hash = generate_password_hash(new)
    db.session.commit()
    return jsonify({"ok": True})
