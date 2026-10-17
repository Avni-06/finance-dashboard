from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.db_models import Budget, Goal
from app.constants import categories_for, BUDGET_TEMPLATES
from app.services.analytics import month_bounds, load_transactions, budget_status
from app.utils.errors import ApiError
from app.utils.security import current_user, login_required, writable
from app.utils.validation import json_body, as_float, as_date, as_str, month_arg

budgets_bp = Blueprint("budgets", __name__)
goals_bp = Blueprint("goals", __name__)


# ---------------- Budgets ----------------
@budgets_bp.get("/")
@login_required
def list_budgets():
    user = current_user()
    y, m = month_arg(request.args.get("month"))
    start, end = month_bounds(y, m)
    rows = budget_status(user.id, load_transactions(user.id, start, end))
    budgeted = {r["category"] for r in rows}
    return jsonify({
        "month": f"{y}-{m:02d}",
        "budgets": rows,
        "unbudgeted_categories": [c for c in categories_for(user.profile_type)["expense"] if c not in budgeted],
        "total_limit": round(sum(r["limit"] for r in rows), 2),
        "total_spent": round(sum(r["spent"] for r in rows), 2),
    })


@budgets_bp.put("/")
@writable
def upsert_budget():
    """Create or update the limit for one category."""
    user = current_user()
    data = json_body()
    category = data.get("category")
    if category not in categories_for(user.profile_type)["expense"]:
        raise ApiError("Pick a valid expense category")
    limit = as_float(data.get("monthly_limit"), "Monthly limit", 1)
    budget = Budget.query.filter_by(user_id=user.id, category=category).first()
    if budget:
        budget.monthly_limit = limit
    else:
        budget = Budget(user_id=user.id, category=category, monthly_limit=limit)
        db.session.add(budget)
    db.session.commit()
    return jsonify({"ok": True, "id": budget.id})


@budgets_bp.delete("/<int:budget_id>")
@writable
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user().id).first()
    if not budget:
        raise ApiError("Budget not found", 404)
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"ok": True})


@budgets_bp.post("/template")
@writable
def apply_template():
    """Fill budgets from the profile's template, based on monthly income."""
    user = current_user()
    if not user.monthly_income:
        raise ApiError("Set your monthly income in Settings first")
    existing = {b.category: b for b in Budget.query.filter_by(user_id=user.id)}
    for category, share in BUDGET_TEMPLATES[user.profile_type or "student"].items():
        limit = round(user.monthly_income * share / 50) * 50 or 50
        if category in existing:
            existing[category].monthly_limit = limit
        else:
            db.session.add(Budget(user_id=user.id, category=category, monthly_limit=limit))
    db.session.commit()
    return jsonify({"ok": True})


# ---------------- Goals ----------------
def _owned_goal(goal_id: int) -> Goal:
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user().id).first()
    if not goal:
        raise ApiError("Goal not found", 404)
    return goal


@goals_bp.get("/")
@login_required
def list_goals():
    goals = Goal.query.filter_by(user_id=current_user().id).order_by(Goal.id).all()
    return jsonify({"goals": [g.to_dict() for g in goals]})


@goals_bp.post("/")
@writable
def create_goal():
    data = json_body()
    goal = Goal(
        user_id=current_user().id,
        name=as_str(data.get("name"), "Goal name", 2, 80),
        target_amount=as_float(data.get("target_amount"), "Target amount", 1),
        saved_amount=as_float(data.get("saved_amount", 0), "Saved amount"),
        deadline=as_date(data.get("deadline"), "Deadline", required=False),
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({"goal": goal.to_dict()}), 201


@goals_bp.patch("/<int:goal_id>")
@writable
def update_goal(goal_id):
    goal = _owned_goal(goal_id)
    data = json_body()
    if "name" in data:
        goal.name = as_str(data["name"], "Goal name", 2, 80)
    if "target_amount" in data:
        goal.target_amount = as_float(data["target_amount"], "Target amount", 1)
    if "saved_amount" in data:
        goal.saved_amount = as_float(data["saved_amount"], "Saved amount")
    if "add_amount" in data:  # quick "add ₹500 to this goal"
        goal.saved_amount = max(goal.saved_amount + as_float(data["add_amount"], "Amount", -10_000_000), 0)
    if "deadline" in data:
        goal.deadline = as_date(data["deadline"], "Deadline", required=False)
    db.session.commit()
    return jsonify({"goal": goal.to_dict()})


@goals_bp.delete("/<int:goal_id>")
@writable
def delete_goal(goal_id):
    db.session.delete(_owned_goal(goal_id))
    db.session.commit()
    return jsonify({"ok": True})
