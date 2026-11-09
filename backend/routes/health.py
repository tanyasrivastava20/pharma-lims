from flask import Blueprint, current_app
from sqlalchemy import text

from database import db
from utils.responses import success

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    db.session.execute(text("SELECT 1"))  # fails loudly if the database is unreachable
    return success({"environment": current_app.config["ENV_NAME"], "database": "connected"},
                   "PharmaLIMS backend is running")
