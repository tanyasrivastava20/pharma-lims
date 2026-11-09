"""Password hashing (bcrypt) and password rules."""
import re

import bcrypt
from flask import current_app

_dummy_hash = None


def hash_password(password):
    rounds = current_app.config.get("BCRYPT_ROUNDS", 12)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("ascii")


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError, AttributeError):
        return False


def fake_verify(password):
    """Takes as long as a real check, so response time doesn't reveal whether a username exists."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("TimingPadding0")
    verify_password(password, _dummy_hash)


def validate_password(password, username=None):
    """Returns a list of problems (empty list = password accepted)."""
    if not isinstance(password, str) or not password:
        return ["Password is required"]
    problems = []
    min_len = current_app.config.get("PASSWORD_MIN_LENGTH", 8)
    if not re.fullmatch(r"[A-Za-z0-9]+", password):
        problems.append("Password may contain only letters and numbers")
    if len(password) < min_len:
        problems.append(f"Password must be at least {min_len} characters")
    if len(password) > 64:
        problems.append("Password must be at most 64 characters")
    if not re.search(r"[a-z]", password):
        problems.append("Password needs at least one lowercase letter")
    if not re.search(r"[A-Z]", password):
        problems.append("Password needs at least one uppercase letter")
    if not re.search(r"[0-9]", password):
        problems.append("Password needs at least one number")
    if username and password.lower() == username.lower():
        problems.append("Password must not be the same as the username")
    return problems
