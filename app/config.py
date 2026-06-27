"""Environment-driven configuration for the Flask app."""
import os
import sys


def _normalize_db_url(url):
    """Neon/Heroku-style 'postgres://' URLs must be 'postgresql://' for SQLAlchemy."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    # Fail fast: a missing SECRET_KEY is a hard configuration error.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        print("FATAL: SECRET_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Production guards: debug off unless explicitly in development, and never
    # leak tracebacks to the client.
    DEBUG = os.environ.get("FLASK_ENV") == "development"
    PROPAGATE_EXCEPTIONS = False

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
