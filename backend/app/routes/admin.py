"""
Admin panel API. Admins see platform-level numbers and manage accounts,
but never individual users' transactions (privacy by design).
"""
import math
from datetime import timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from app.extensions import db
from app.models.db_models import User, Transaction, ModelRun, MerchantRule, Insight, utcnow
from app.ml.classifier import model_metrics, set_model
from app.ml.concepts import CATEGORY_TO_CONCEPT
from app.ml.train import train
from app.utils.errors import ApiError
from app.utils.security import current_user, roles_required
from app.utils.validation import json_body

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/stats")
@roles_required("admin")
def stats():
    now = utcnow()
    users = User.query.filter(User.role == "user")
    by_profile = dict(db.session.query(User.profile_type, func.count(User.id))
                      .filter(User.role == "user").group_by(User.profile_type).all())
    by_source = dict(db.session.query(Transaction.category_source, func.count(Transaction.id))
                     .group_by(Transaction.category_source).all())
    by_upload = dict(db.session.query(Transaction.source, func.count(Transaction.id))
                     .group_by(Transaction.source).all())

    # Signups per week, last 8 weeks
    signups = []
    for i in range(7, -1, -1):
        start = now - timedelta(weeks=i + 1)
        end = now - timedelta(weeks=i)
        signups.append({
            "week": end.date().isoformat(),
            "count": users.filter(User.created_at > start, User.created_at <= end).count(),
        })

    return jsonify({
        "users": {
            "total": users.count(),
            "active_7d": users.filter(User.last_login_at >= now - timedelta(days=7)).count(),
            "deactivated": users.filter(User.is_active.is_(False)).count(),
            "onboarded": users.filter(User.onboarded.is_(True)).count(),
            "by_profile": {k or "not set": v for k, v in by_profile.items()},
        },
        "transactions": {
            "total": Transaction.query.count(),
            "by_category_source": {k or "unknown": v for k, v in by_source.items()},
            "by_upload_source": {k or "unknown": v for k, v in by_upload.items()},
            "user_corrections": Transaction.query.filter_by(is_overridden=True).count(),
            "merchant_rules": MerchantRule.query.count(),
        },
        "insights": {
            "total": Insight.query.count(),
            "by_source": dict(db.session.query(Insight.source, func.count(Insight.id))
                              .group_by(Insight.source).all()),
        },
        "signups": signups,
    })


@admin_bp.get("/users")
@roles_required("admin")
def list_users():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = 20
    q = User.query
    if request.args.get("q"):
        like = f"%{request.args['q'].strip()[:60]}%"
        q = q.filter(or_(User.email.ilike(like), User.name.ilike(like)))
    if request.args.get("profile_type"):
        q = q.filter(User.profile_type == request.args["profile_type"])
    if request.args.get("role"):
        q = q.filter(User.role == request.args["role"])

    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    counts = dict(db.session.query(Transaction.user_id, func.count(Transaction.id))
                  .filter(Transaction.user_id.in_([u.id for u in users]))
                  .group_by(Transaction.user_id).all())
    return jsonify({
        "users": [{
            **{k: v for k, v in u.to_dict().items() if k in
               ("id", "email", "name", "role", "profile_type", "is_active", "onboarded", "created_at")},
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "transaction_count": counts.get(u.id, 0),
        } for u in users],
        "total": total,
        "pages": max(math.ceil(total / per_page), 1),
    })


@admin_bp.patch("/users/<int:user_id>")
@roles_required("admin")
def update_user(user_id):
    target = db.session.get(User, user_id)
    if not target:
        raise ApiError("User not found", 404)
    if target.id == current_user().id:
        raise ApiError("You can't change your own account here")
    if target.role == "admin":
        raise ApiError("Admins can't be deactivated from the panel")
    data = json_body()
    if "is_active" in data:
        target.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify({"ok": True, "is_active": target.is_active})


@admin_bp.get("/model")
@roles_required("admin")
def model_info():
    runs = ModelRun.query.order_by(ModelRun.created_at.desc()).limit(10).all()
    pending = Transaction.query.filter_by(is_overridden=True).count()
    return jsonify({
        "current": model_metrics(),
        "runs": [r.to_dict() for r in runs],
        "available_corrections": pending,
    })


@admin_bp.post("/model/retrain")
@roles_required("admin")
def retrain():
    """Retrain on synthetic data + every user correction (description -> concept)."""
    rows = (db.session.query(Transaction.description, Transaction.category, User.profile_type)
            .join(User, User.id == Transaction.user_id)
            .filter(Transaction.is_overridden.is_(True), User.role == "user").all())
    corrections = []
    for desc, category, ptype in rows:
        concept = CATEGORY_TO_CONCEPT.get(ptype or "student", {}).get(category)
        if concept:
            corrections.append((desc, concept))

    result = train(corrections)
    set_model(result["model"])
    m = result["metrics"]
    db.session.add(ModelRun(accuracy=m["accuracy"], macro_f1=m["macro_f1"],
                            n_samples=m["n_samples"], n_user_corrections=m["n_user_corrections"]))
    db.session.commit()
    return jsonify({"ok": True, "metrics": m})
