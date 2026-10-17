from datetime import date
from flask import request
from app.utils.errors import ApiError


def json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be JSON")
    return data


def as_float(value, field: str, lo: float = 0, hi: float = 10_000_000) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ApiError(f"{field} must be a number")
    if v != v or not lo <= v <= hi:  # v != v catches NaN
        raise ApiError(f"{field} must be between {lo:g} and {hi:g}")
    return v


def as_int(value, field: str, lo: int, hi: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ApiError(f"{field} must be a whole number")
    if not lo <= v <= hi:
        raise ApiError(f"{field} must be between {lo} and {hi}")
    return v


def as_date(value, field: str, required: bool = True) -> date | None:
    if value in (None, ""):
        if required:
            raise ApiError(f"{field} is required")
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ApiError(f"{field} must be a date like 2026-01-31")


def as_str(value, field: str, lo: int = 1, hi: int = 255) -> str:
    s = str(value or "").strip()
    if not lo <= len(s) <= hi:
        raise ApiError(f"{field} must be {lo}-{hi} characters")
    return s


def month_arg(value: str | None) -> tuple[int, int]:
    """'2026-10' -> (2026, 10). Defaults to the current month."""
    if not value:
        t = date.today()
        return t.year, t.month
    try:
        y, m = value.split("-")
        y, m = int(y), int(m)
        if not 1 <= m <= 12:
            raise ValueError
        return y, m
    except ValueError:
        raise ApiError("month must look like 2026-10")
