"""JWT setup and the decorator that protects routes by role."""
from functools import wraps

from flask import g, request
from flask_jwt_extended import JWTManager, current_user, verify_jwt_in_request

from database import db
from models import RevokedToken, User
from utils.responses import error
from utils.logging_setup import audit

jwt = JWTManager()


def init_jwt(app):
    jwt.init_app(app)


@jwt.user_lookup_loader
def _load_user(_header, payload):
    return db.session.get(User, int(payload["sub"]))


@jwt.token_in_blocklist_loader
def _is_revoked(_header, payload):
    return db.session.query(RevokedToken.id).filter_by(jti=payload["jti"]).first() is not None


def _auth_failure(what):
    audit.warning("Auth failure: %s (%s %s) ip=%s", what, request.method, request.path, request.remote_addr)


@jwt.unauthorized_loader
def _missing_token(_reason):
    _auth_failure("no token sent")
    return error("Authentication required", 401)


@jwt.invalid_token_loader
def _invalid_token(reason):
    _auth_failure(f"invalid token - {reason}")
    return error("Invalid token", 401)


@jwt.expired_token_loader
def _expired_token(_header, payload):
    _auth_failure(f"expired token for user id {payload.get('sub')}")
    return error("Token has expired", 401)


@jwt.revoked_token_loader
def _revoked_token(_header, payload):
    _auth_failure(f"logged-out token used by user id {payload.get('sub')}")
    return error("Token has been revoked", 401)


@jwt.user_lookup_error_loader
def _unknown_user(_header, payload):
    _auth_failure(f"token for deleted user id {payload.get('sub')}")
    return error("Account no longer exists", 401)


def role_required(*roles):
    """@role_required() = any logged-in user. @role_required("Admin") = Admin only, and so on.

    The role is read from the database on every request, so deactivating an account
    or changing its role takes effect immediately, even for tokens already issued.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user
            g.log_user = user.username
            if not user.is_active:
                return error("Account is deactivated", 403)
            if roles and user.role not in roles:
                audit.warning("Permission denied: %s (%s) tried %s", user.username, user.role, fn.__name__)
                return error("Permission denied", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
