from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.extensions import jwt


class ApiError(Exception):
    """Raise ApiError("message", status) from any route to return a JSON error."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(e):
        return jsonify({"error": e.message}), e.status

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify({"error": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception(e)
        return jsonify({"error": "Something went wrong on our side"}), 500

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return jsonify({"error": "Please log in"}), 401

    @jwt.invalid_token_loader
    def bad_token(_reason):
        return jsonify({"error": "Invalid session, please log in again"}), 401

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return jsonify({"error": "Session expired, please log in again"}), 401
