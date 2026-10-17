import csv
import io
import math
from datetime import date, timedelta

from flask import Blueprint, jsonify, request, Response
from sqlalchemy import func, or_

from app.extensions import db
from app.models.db_models import Transaction
from app.constants import categories_for, TX_TYPES
from app.ml.classifier import categorize
from app.services.analytics import month_bounds
from app.services.transactions import import_rows, apply_correction, user_rules
from app.utils.csv_parser import parse_csv
from app.utils.errors import ApiError
from app.utils.merchant import merchant_key
from app.utils.security import current_user, login_required, writable
from app.utils.validation import json_body, as_float, as_date, as_str, month_arg

tx_bp = Blueprint("transactions", __name__)

SORTS = {
    "date_desc": (Transaction.date.desc(), Transaction.id.desc()),
    "date_asc": (Transaction.date.asc(), Transaction.id.asc()),
    "amount_desc": (Transaction.amount.desc(),),
    "amount_asc": (Transaction.amount.asc(),),
}


def _get_owned(tx_id: int) -> Transaction:
    # Always scope by user_id so nobody can read/edit someone else's row by guessing ids
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user().id).first()
    if not tx:
        raise ApiError("Transaction not found", 404)
    return tx


def _filtered_query():
    user = current_user()
    q = Transaction.query.filter(Transaction.user_id == user.id)
    args = request.args
    if args.get("month"):
        start, end = month_bounds(*month_arg(args["month"]))
        q = q.filter(Transaction.date.between(start, end))
    if args.get("from"):
        q = q.filter(Transaction.date >= as_date(args["from"], "from"))
    if args.get("to"):
        q = q.filter(Transaction.date <= as_date(args["to"], "to"))
    if args.get("category"):
        q = q.filter(Transaction.category == args["category"])
    if args.get("type") in TX_TYPES:
        q = q.filter(Transaction.type == args["type"])
    if args.get("q"):
        like = f"%{args['q'].strip()[:60]}%"
        q = q.filter(or_(Transaction.description.ilike(like), Transaction.merchant.ilike(like),
                         Transaction.note.ilike(like)))
    if args.get("review") == "1":
        q = q.filter(Transaction.category_source == "ml", Transaction.category_confidence < 0.6)
    return q


@tx_bp.get("/")
@login_required
def list_transactions():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 25, type=int), 1), 100)
    sort = SORTS.get(request.args.get("sort", "date_desc"), SORTS["date_desc"])

    q = _filtered_query()
    totals = dict(
        q.with_entities(Transaction.type, func.sum(Transaction.amount))
        .group_by(Transaction.type).all()
    )
    total = q.count()
    items = q.order_by(*sort).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        "transactions": [t.to_dict() for t in items],
        "total": total,
        "page": page,
        "pages": max(math.ceil(total / per_page), 1),
        "summary": {
            "income": round(totals.get("income", 0) or 0, 2),
            "expense": round(totals.get("expense", 0) or 0, 2),
        },
    })


@tx_bp.post("/upload")
@writable
def upload_csv():
    file = request.files.get("file")
    if not file or not file.filename:
        raise ApiError("No file uploaded")
    if not file.filename.lower().endswith((".csv", ".txt")):
        raise ApiError("Please upload a .csv file")
    try:
        parsed = parse_csv(file.read())
    except ValueError as e:
        raise ApiError(str(e), 422)

    result = import_rows(current_user(), parsed["rows"])
    result.update({"skipped": parsed["skipped"], "warnings": parsed["warnings"]})
    return jsonify(result), 201


@tx_bp.post("/")
@writable
def create_transaction():
    user = current_user()
    data = json_body()
    tx_type = data.get("type")
    if tx_type not in TX_TYPES:
        raise ApiError("type must be income or expense")
    description = as_str(data.get("description"), "Description", 1, 255)
    amount = as_float(data.get("amount"), "Amount", 0.01)
    tx_date = as_date(data.get("date"), "Date")
    # +1 day of slack: the server may run in UTC while the user is in IST (UTC+5:30)
    if tx_date > date.today() + timedelta(days=1):
        raise ApiError("Date can't be in the future")

    category = data.get("category")
    if category:
        if category not in categories_for(user.profile_type)[tx_type]:
            raise ApiError("Invalid category for this transaction type")
        result = {"merchant": merchant_key(description), "confidence": 1.0, "source": "manual"}
    else:
        result = categorize(description, tx_type, user.profile_type, user_rules(user.id))
        category = result["category"]

    tx = Transaction(
        user_id=user.id, date=tx_date, description=description, amount=round(amount, 2),
        type=tx_type, category=category, merchant=result["merchant"] or None,
        category_confidence=result["confidence"], category_source=result["source"],
        source="manual", note=(str(data.get("note") or "").strip()[:255] or None),
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify({"transaction": tx.to_dict()}), 201


@tx_bp.patch("/<int:tx_id>")
@writable
def update_transaction(tx_id):
    user = current_user()
    tx = _get_owned(tx_id)
    data = json_body()

    if "description" in data:
        tx.description = as_str(data["description"], "Description", 1, 255)
        tx.merchant = merchant_key(tx.description) or None
    if "amount" in data:
        tx.amount = round(as_float(data["amount"], "Amount", 0.01), 2)
    if "date" in data:
        tx.date = as_date(data["date"], "Date")
    if "type" in data:
        if data["type"] not in TX_TYPES:
            raise ApiError("type must be income or expense")
        tx.type = data["type"]
    if "note" in data:
        tx.note = str(data["note"] or "").strip()[:255] or None

    similar_updated = 0
    if "category" in data and data["category"] != tx.category:
        if data["category"] not in categories_for(user.profile_type)[tx.type]:
            raise ApiError("Invalid category for this transaction type")
        similar_updated = apply_correction(user, tx, data["category"], bool(data.get("apply_to_similar", True)))
    db.session.commit()
    return jsonify({"transaction": tx.to_dict(), "similar_updated": similar_updated})


@tx_bp.delete("/<int:tx_id>")
@writable
def delete_transaction(tx_id):
    tx = _get_owned(tx_id)
    db.session.delete(tx)
    db.session.commit()
    return jsonify({"ok": True})


@tx_bp.get("/categories")
@login_required
def categories():
    user = current_user()
    return jsonify({"profile_type": user.profile_type, **categories_for(user.profile_type)})


@tx_bp.get("/export")
@login_required
def export_csv():
    rows = _filtered_query().order_by(Transaction.date.desc()).limit(10000).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "Description", "Type", "Amount", "Category", "Note"])
    for t in rows:
        w.writerow([t.date.isoformat(), t.description, t.type, f"{t.amount:.2f}", t.category, t.note or ""])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=finsight-transactions.csv"})
