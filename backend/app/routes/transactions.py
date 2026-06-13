from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.db_models import Transaction
from app.utils.csv_parser import parse_csv
from app.ml.classifier import classify_transaction

tx_bp = Blueprint("transactions", __name__)

@tx_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_csv():
    user_id = int(get_jwt_identity())
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    try:
        rows = parse_csv(file.read())
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    new_count = 0
    for row in rows:
        result = classify_transaction(str(row["description"]))
        tx = Transaction(
            user_id=user_id,
            date=row["date"].date(),
            description=str(row["description"]),
            amount=float(row["amount"]),
            category=result["category"],
            category_confidence=result["confidence"],
        )
        db.session.add(tx)
        new_count += 1

    db.session.commit()
    return jsonify({"imported": new_count}), 201

@tx_bp.route("/", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    category = request.args.get("category")

    q = Transaction.query.filter_by(user_id=user_id)
    if category:
        q = q.filter_by(category=category)
    paginated = q.order_by(Transaction.date.desc()).paginate(page=page, per_page=per_page)

    return jsonify({
        "transactions": [
            {
                "id": t.id, "date": str(t.date), "description": t.description,
                "amount": t.amount, "category": t.category,
                "confidence": t.category_confidence
            } for t in paginated.items
        ],
        "total": paginated.total,
        "pages": paginated.pages,
    })

@tx_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    user_id = int(get_jwt_identity())
    txns = Transaction.query.filter_by(user_id=user_id).all()
    by_category = {}
    for t in txns:
        by_category[t.category] = by_category.get(t.category, 0) + abs(t.amount)
    return jsonify({
        "by_category": by_category,
        "total_spent": sum(abs(t.amount) for t in txns if t.amount < 0),
        "total_income": sum(t.amount for t in txns if t.amount > 0),
        "transaction_count": len(txns),
    })