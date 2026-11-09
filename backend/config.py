"""Application configuration. Values come from the .env file (see .env.example)."""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

_DEV_SECRET = "dev-only-secret-change-me-0123456789-abcdef"
_DEV_JWT_SECRET = "dev-only-jwt-secret-change-me-0123456789-abcdef"


class Config:
    # --- Security ---
    SECRET_KEY = os.getenv("SECRET_KEY", _DEV_SECRET)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEV_JWT_SECRET)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", "8")))
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # --- Database (a relative sqlite path is created inside the instance/ folder) ---
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pharmalims.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 1_500_000  # largest upload accepted (CSV import), in bytes

    # --- CORS: the React dev server address(es), comma separated ---
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

    # --- Logging (used in the logging step) ---
    LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "logs"))
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "5000000"))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    LOG_TO_FILES = True
    LOG_TO_CONSOLE = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    DEBUG = False
    TESTING = False
    ENV_NAME = "base"

    @classmethod
    def validate(cls):
        """Hook for environment-specific safety checks."""


class DevelopmentConfig(Config):
    DEBUG = True
    ENV_NAME = "development"


class TestingConfig(Config):
    TESTING = True
    ENV_NAME = "testing"
    BCRYPT_ROUNDS = 4  # fast hashing for automated tests only
    LOG_TO_FILES = False
    LOG_TO_CONSOLE = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    ENV_NAME = "production"

    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == _DEV_SECRET or cls.JWT_SECRET_KEY == _DEV_JWT_SECRET:
            raise RuntimeError("Set SECRET_KEY and JWT_SECRET_KEY in .env before running in production.")


_CONFIGS = {"development": DevelopmentConfig, "testing": TestingConfig, "production": ProductionConfig}


def get_config(name=None):
    name = (name or os.getenv("FLASK_ENV", "development")).lower()
    return _CONFIGS.get(name, DevelopmentConfig)
