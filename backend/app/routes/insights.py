from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.db_models import Insight, utcnow
from app.services.ai import generate_report, providers_status, week_bounds
from app.utils.errors import ApiError
from app.utils.security import current_user, login_required

insights_bp = Blueprint("insights", __name__)
DAILY_LIMIT = 5  # protects the free-tier API quota


@insights_bp.get("/")
@login_required
def list_insights():
    user = current_user()
    rows = (Insight.query.filter_by(user_id=user.id)
            .order_by(Insight.created_at.desc()).limit(12).all())
    return jsonify({"insights": [i.to_dict() for i in rows], "providers": providers_status()})


@insights_bp.post("/generate")
@login_required
def generate():
    """Returns this week's report (cached). Pass {"force": true} to regenerate.
    Demo users can generate too (it's the best part of the demo), but it's rate-limited."""
    user = current_user()
    force = bool((request.get_json(silent=True) or {}).get("force"))
    w_start, w_end = week_bounds(date.today())

    latest = (Insight.query.filter_by(user_id=user.id, period_start=w_start)
              .order_by(Insight.created_at.desc()).first())
    if latest and not force:
        return jsonify({"insight": latest.to_dict(), "cached": True})

    recent = Insight.query.filter(Insight.user_id == user.id,
                                  Insight.created_at >= utcnow() - timedelta(days=1)).count()
    if recent >= DAILY_LIMIT:
        raise ApiError("You've hit today's report limit. Try again tomorrow.", 429)

    content, source, _ctx = generate_report(user)
    insight = Insight(user_id=user.id, period_start=w_start, period_end=w_end,
                      content=content, source=source)
    db.session.add(insight)
    db.session.commit()
    return jsonify({"insight": insight.to_dict(), "cached": False}), 201
