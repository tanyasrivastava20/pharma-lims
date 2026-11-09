"""Database setup: one shared SQLAlchemy object used by every model and route."""
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _record):
    """SQLite ignores foreign keys unless this is switched on for every connection."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db(app):
    db.init_app(app)
    import models  # noqa: F401  (importing registers every model with SQLAlchemy)

    with app.app_context():
        db.create_all()
