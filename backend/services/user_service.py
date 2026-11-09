import re


from database import db
from models import ROLES, User
from utils.responses import APIError
from utils.security import hash_password, validate_password
from utils.validation import clean_text as _text
from utils.logging_setup import audit

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,50}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_new_user(data):
    errors = {}
    username = (_text(data, "username", 50, errors, True) or "").lower()
    if username and "username" not in errors and not USERNAME_RE.match(username):
        errors["username"] = "3-50 characters: letters, numbers, dot, dash or underscore"
    full_name = _text(data, "full_name", 100, errors, True)
    email = _text(data, "email", 120, errors)
    if email and "email" not in errors:
        email = email.lower()
        if not EMAIL_RE.match(email):
            errors["email"] = "Not a valid email address"
    employee_id = _text(data, "employee_id", 30, errors)
    department = _text(data, "department", 80, errors)
    role = data.get("role")
    if role not in ROLES:
        errors["role"] = "Must be one of: " + ", ".join(ROLES)
    is_active = data.get("is_active", True)
    if not isinstance(is_active, bool):
        errors["is_active"] = "Must be true or false"
    password = data.get("password")
    problems = validate_password(password, username)
    if problems:
        errors["password"] = "; ".join(problems)
    if errors:
        raise APIError("Validation failed", 400, errors)
    return dict(username=username, password=password, role=role, full_name=full_name, email=email,
                employee_id=employee_id, department=department, is_active=is_active)


def create_user(data):
    clean = validate_new_user(data)
    errors = {}
    if User.query.filter_by(username=clean["username"]).first():
        errors["username"] = "Username already exists"
    if clean["email"] and User.query.filter_by(email=clean["email"]).first():
        errors["email"] = "Email already in use"
    if clean["employee_id"] and User.query.filter_by(employee_id=clean["employee_id"]).first():
        errors["employee_id"] = "Employee ID already in use"
    if errors:
        raise APIError("Duplicate values", 409, errors)
    password = clean.pop("password")
    user = User(password_hash=hash_password(password), **clean)
    db.session.add(user)
    db.session.commit()
    audit.info("User created: %s (%s)", user.username, user.role)
    return user


# ---------------------------------------------------------------- admin user management
def build_user_query():
    """Applies ?q= ?role= ?is_active= ?sort= ?order= from the URL."""
    from flask import request
    from utils.query import apply_sort, bool_arg, like_pattern

    query = User.query
    q = (request.args.get("q") or "").strip()
    if q:
        pattern = like_pattern(q)
        query = query.filter(db.or_(*[getattr(User, f).ilike(pattern, escape="\\")
                                      for f in ("username", "full_name", "email", "employee_id")]))
    role = request.args.get("role")
    if role:
        if role not in ROLES:
            raise APIError("'role' must be one of: " + ", ".join(ROLES), 400)
        query = query.filter(User.role == role)
    active = bool_arg("is_active")
    if active is not None:
        query = query.filter(User.is_active == active)
    return apply_sort(query, User, ("username", "full_name", "role", "is_active", "created_at"), "username")


def validate_user_update(data):
    errors, changes = {}, {}
    if "password" in data:
        errors["password"] = "Passwords are changed with the reset-password endpoint"
    if "full_name" in data:
        value = _text(data, "full_name", 100, errors, True)
        if "full_name" not in errors:
            changes["full_name"] = value
    for key, max_len in (("email", 120), ("employee_id", 30), ("department", 80)):
        if key in data:
            value = _text(data, key, max_len, errors)
            if key == "email" and value and key not in errors:
                value = value.lower()
                if not EMAIL_RE.match(value):
                    errors["email"] = "Not a valid email address"
            if key not in errors:
                changes[key] = value
    if "role" in data:
        if data["role"] not in ROLES:
            errors["role"] = "Must be one of: " + ", ".join(ROLES)
        else:
            changes["role"] = data["role"]
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            errors["is_active"] = "Must be true or false"
        else:
            changes["is_active"] = data["is_active"]
    return changes, errors


def update_user(user, data, actor):
    changes, errors = validate_user_update(data)
    if "username" in data and str(data["username"]).strip().lower() != user.username:
        errors["username"] = "Username cannot be changed"
    if user.id == actor.id:
        if "role" in changes and changes["role"] != user.role:
            errors["role"] = "You cannot change your own role"
        if changes.get("is_active") is False:
            errors["is_active"] = "You cannot deactivate your own account"
    if errors:
        raise APIError("Validation failed", 400, errors)

    dupes = {}
    for key in ("email", "employee_id"):
        if changes.get(key) and User.query.filter(getattr(User, key) == changes[key], User.id != user.id).first():
            dupes[key] = "Already in use"
    if dupes:
        raise APIError("Duplicate values", 409, dupes)

    old_role, old_active = user.role, user.is_active
    for key, value in changes.items():
        setattr(user, key, value)
    db.session.commit()
    audit.info("User updated by %s: %s fields=%s", actor.username, user.username, sorted(changes))
    if user.role != old_role:
        audit.info("Role changed by %s: %s %s -> %s", actor.username, user.username, old_role, user.role)
    if user.is_active != old_active:
        audit.info("Account %s by %s: %s", "activated" if user.is_active else "deactivated",
                                actor.username, user.username)
    return user


def reset_password(user, new_password, actor):
    problems = validate_password(new_password, user.username)
    if problems:
        raise APIError("Validation failed", 400, {"new_password": "; ".join(problems)})
    user.password_hash = hash_password(new_password)
    db.session.commit()
    audit.info("Password reset by %s for %s", actor.username, user.username)


def delete_user(user, actor):
    if user.id == actor.id:
        raise APIError("You cannot delete your own account", 400)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    audit.info("User deleted by %s: %s", actor.username, username)
