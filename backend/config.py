import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_SECRET = "dev-only-secret-change-me-in-production-please"


def _db_url() -> str:
    url = os.getenv("DATABASE_URL") or "sqlite:///finsight.db"
    # Neon/Render sometimes hand out "postgres://", SQLAlchemy needs "postgresql://"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", _DEFAULT_SECRET)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_DATABASE_URI = _db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if o.strip()
    ]
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB CSV upload limit

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if APP_ENV == "production" and SECRET_KEY == _DEFAULT_SECRET:
        raise RuntimeError("Set SECRET_KEY in production")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    GROQ_API_KEY = None
    GEMINI_API_KEY = None
