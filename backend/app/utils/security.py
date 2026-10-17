from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.extensions import db
from app.models.db_models import User
from app.utils.errors import ApiError


def current_user() -> User:
    """Loads the user from the DB (not just the token) so deactivation and
    role changes apply immediately. Cached per request on flask.g."""
    if getattr(g, "_current_user", None) is not None:
        return g._current_user
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or not user.is_active:
        raise ApiError("Account not found or deactivated", 401)
    g._current_user = user
    return user


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user()
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    """@roles_required("admin") -> only those roles get through."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if current_user().role not in roles:
                raise ApiError("You don't have permission to do that", 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def writable(fn):
    """Demo accounts are read-only. Put this on every route that changes data."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if current_user().role == "demo":
            raise ApiError("Demo account is read-only. Sign up to save your own data.", 403)
        return fn(*args, **kwargs)
    return wrapper
