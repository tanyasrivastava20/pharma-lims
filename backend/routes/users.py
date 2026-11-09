"""User management. Every route here is Admin only."""
from flask_jwt_extended import current_user

from database import db
from middleware.auth import role_required
from models import User
from models.constants import ADMIN
from services import user_service
from utils.query import paginate
from utils.responses import APIError, success
from utils.validation import get_json_body

from flask import Blueprint

users_bp = Blueprint("users", __name__)


def _get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise APIError("User not found", 404)
    return user


@users_bp.get("")
@role_required(ADMIN)
def list_users():
    return success(paginate(user_service.build_user_query(), lambda u: u.to_dict()))


@users_bp.post("")
@role_required(ADMIN)
def create_user():
    user = user_service.create_user(get_json_body())
    return success(user.to_dict(), "User created", 201)


@users_bp.get("/<int:user_id>")
@role_required(ADMIN)
def get_user(user_id):
    return success(_get_user(user_id).to_dict())


@users_bp.put("/<int:user_id>")
@role_required(ADMIN)
def update_user(user_id):
    user = user_service.update_user(_get_user(user_id), get_json_body(), current_user)
    return success(user.to_dict(), "User updated")


@users_bp.delete("/<int:user_id>")
@role_required(ADMIN)
def delete_user(user_id):
    user_service.delete_user(_get_user(user_id), current_user)
    return success(message="User deleted")


@users_bp.post("/<int:user_id>/reset-password")
@role_required(ADMIN)
def reset_password(user_id):
    data = get_json_body()
    user_service.reset_password(_get_user(user_id), data.get("new_password"), current_user)
    return success(message="Password reset")
