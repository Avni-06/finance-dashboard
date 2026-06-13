from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.db_models import Insight, Transaction
from app.utils.openai_client import generate_weekly_insight
from datetime import date, timedelta

insights_bp = Blueprint("insights", __name__)

@insights_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate():
    user_id = int(get_jwt_identity())
    week_start = date.today() - timedelta(days=date.today().weekday())

    # Check if already generated this week
    existing = Insight.query.filter_by(user_id=user_id, week_start=week_start).first()
    if existing:
        return jsonify({"insight": existing.content, "cached": True})

    # Gather stats
    txns = Transaction.query.filter_by(user_id=user_id).all()
    by_category = {}
    for t in txns:
        by_category[t.category] = by_category.get(t.category, 0) + abs(t.amount)
    stats = {
        "by_category": by_category,
        "total_spent": sum(abs(t.amount) for t in txns if t.amount < 0),
        "total_income": sum(t.amount for t in txns if t.amount > 0),
        "transaction_count": len(txns),
    }
    tx_dicts = [{"description": t.description, "amount": t.amount, "category": t.category} for t in txns[-50:]]

    content = generate_weekly_insight(stats, tx_dicts)
    insight = Insight(user_id=user_id, week_start=week_start, content=content)
    db.session.add(insight)
    db.session.commit()

    return jsonify({"insight": content, "cached": False})

@insights_bp.route("/", methods=["GET"])
@jwt_required()
def list_insights():
    user_id = int(get_jwt_identity())
    insights = Insight.query.filter_by(user_id=user_id).order_by(Insight.week_start.desc()).limit(8).all()
    return jsonify([
        {"id": i.id, "week_start": str(i.week_start), "content": i.content}
        for i in insights
    ])