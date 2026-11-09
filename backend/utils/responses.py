"""One JSON format for every response: {"success": bool, "message": str, "data": ...}."""
from flask import jsonify


class APIError(Exception):
    """Raise this anywhere in the backend to return a clean JSON error."""

    def __init__(self, message, status=400, errors=None):
        super().__init__(message)
        self.message, self.status, self.errors = message, status, errors


def success(data=None, message="", status=200):
    return jsonify({"success": True, "message": message, "data": {} if data is None else data}), status


def error(message, status=400, errors=None):
    body = {"success": False, "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status
