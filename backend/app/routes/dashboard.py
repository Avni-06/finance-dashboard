from flask import Blueprint, jsonify, request

from app.services.analytics import dashboard
from app.utils.security import current_user, login_required
from app.utils.validation import month_arg

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@login_required
def get_dashboard():
    y, m = month_arg(request.args.get("month"))
    return jsonify(dashboard(current_user(), y, m))
