from flask import g, request

from database import db
from models import User
from utils.responses import APIError
from utils.security import fake_verify, hash_password, validate_password, verify_password
from utils.logging_setup import audit


def authenticate(username, password):
    """Returns the user, or raises APIError (401 wrong details, 403 deactivated)."""
    username = username.strip().lower()
    user = User.query.filter_by(username=username).first()
    if user is None:
        fake_verify(password)
        ok = False
    else:
        ok = verify_password(password, user.password_hash)
    if not ok:
        audit.warning("Failed login for username=%s from %s", username, request.remote_addr)
        raise APIError("Invalid username or password", 401)
    if not user.is_active:
        audit.warning("Login refused (deactivated account): %s", username)
        raise APIError("Account is deactivated", 403)
    g.log_user = user.username
    audit.info("Login OK: %s (%s) from %s", user.username, user.role, request.remote_addr)
    return user


def change_password(user, current_password, new_password):
    if not isinstance(current_password, str) or not verify_password(current_password, user.password_hash):
        audit.warning("Password change refused (wrong current password): %s", user.username)
        raise APIError("Current password is incorrect", 400)
    problems = validate_password(new_password, user.username)
    if not problems and new_password == current_password:
        problems = ["New password must be different from the current password"]
    if problems:
        raise APIError("Validation failed", 400, {"new_password": "; ".join(problems)})
    user.password_hash = hash_password(new_password)
    db.session.commit()
    audit.info("Password changed: %s", user.username)
