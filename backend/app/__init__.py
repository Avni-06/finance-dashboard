from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from app.extensions import db, jwt
from app.utils.errors import register_error_handlers


def create_app(config_class=Config):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"])
    register_error_handlers(app)

    from app.models import db_models  # noqa: F401  (registers tables)
    from app.routes.auth import auth_bp
    from app.routes.transactions import tx_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.budgets import budgets_bp, goals_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tx_bp, url_prefix="/api/transactions")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(budgets_bp, url_prefix="/api/budgets")
    app.register_blueprint(goals_bp, url_prefix="/api/goals")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    with app.app_context():
        db.create_all()

    return app
