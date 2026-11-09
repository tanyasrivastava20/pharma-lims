from sqlalchemy import CheckConstraint

from database import db
from models.base import DictMixin, TimestampMixin
from models.constants import ROLES, sql_in_list


class User(db.Model, TimestampMixin, DictMixin):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint(f"role IN ({sql_in_list(ROLES)})", name="ck_users_role"),)
    _hidden = ("password_hash",)  # the hash is never sent to the browser

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    employee_id = db.Column(db.String(30), unique=True)
    department = db.Column(db.String(80))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
