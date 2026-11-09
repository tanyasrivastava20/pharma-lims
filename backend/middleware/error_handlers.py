"""Turns every error into the standard JSON format (no HTML error pages, no stack traces)."""
from flask import g
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from database import db
from utils.responses import APIError, error

_MESSAGES = {
    400: "Bad request",
    401: "Authentication required",
    403: "Permission denied",
    404: "Resource not found",
    405: "Method not allowed",
    413: "File is too large (limit about 1.5 MB)",
    415: "Unsupported media type",
}


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(e):
        return error(e.message, e.status, e.errors)

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return error(_MESSAGES.get(e.code, e.name), e.code)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        db.session.rollback()
        app.logger.warning("Database integrity error: %s", e.orig)
        return error("This record conflicts with existing data (duplicate or invalid reference)", 409)

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(e):
        db.session.rollback()
        app.logger.exception("Database error: %s", e)
        return error("Database error", 500)

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception("Unhandled error: %s", e)
        return error(f"Internal server error (reference {getattr(g, 'request_id', '-')})", 500)
