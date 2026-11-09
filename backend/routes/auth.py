from datetime import datetime, timezone

from flask import Blueprint, current_app
from flask_jwt_extended import create_access_token, current_user, get_jwt

from database import db
from middleware.auth import role_required
from models import RevokedToken
from models.base import utcnow
from models.constants import ADMIN
from services import auth_service, user_service
from utils.responses import APIError, success
from utils.validation import get_json_body
from utils.logging_setup import audit

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = get_json_body()
    username, password = data.get("username"), data.get("password")
    if not isinstance(username, str) or not isinstance(password, str) or not username.strip() or not password:
        raise APIError("Username and password are required", 400)
    user = auth_service.authenticate(username, password)
    token = create_access_token(identity=str(user.id),
                                additional_claims={"role": user.role, "username": user.username})
    return success({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
        "user": user.to_dict(),
    }, "Login successful")


@auth_bp.post("/register")
@role_required(ADMIN)
def register():
    """Creates an account. Admin only, so nobody can sign themselves up as an Admin."""
    user = user_service.create_user(get_json_body())
    return success(user.to_dict(), "User created", 201)


@auth_bp.post("/logout")
@role_required()
def logout():
    claims = get_jwt()
    expires = datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None)
    db.session.add(RevokedToken(jti=claims["jti"], expires_at=expires))
    RevokedToken.query.filter(RevokedToken.expires_at < utcnow()).delete()  # tidy up old entries
    db.session.commit()
    audit.info("Logout: %s", current_user.username)
    return success(message="Logged out")


@auth_bp.get("/me")
@role_required()
def me():
    """Also used by the frontend to check that a saved token is still valid."""
    return success(current_user.to_dict())


@auth_bp.post("/change-password")
@role_required()
def change_password():
    data = get_json_body()
    auth_service.change_password(current_user, data.get("current_password"), data.get("new_password"))
    return success(message="Password changed")
