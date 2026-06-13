from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=["http://localhost:3000"])

    from app.routes.auth import auth_bp
    from app.routes.transactions import tx_bp
    from app.routes.insights import insights_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tx_bp, url_prefix="/api/transactions")
    app.register_blueprint(insights_bp, url_prefix="/api/insights")

    with app.app_context():
        db.create_all()

    return app