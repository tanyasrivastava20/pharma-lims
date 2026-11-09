"""Creates the three starter accounts. Safe to run more than once.

Run from the backend folder:
    python seed.py            starter accounts only
    python seed.py --demo     also adds demo master data and products (for trying the API)
Passwords come from .env (SEED_*_PASSWORD) or the defaults below. Change them after first login.
"""
import os
import sys

from app import create_app
from models import User
from services.user_service import create_user
from utils.demo_data import seed_demo

STARTERS = [
    dict(username="admin", role="Admin", full_name="System Administrator", employee_id="EMP001",
         department="Administration", env="SEED_ADMIN_PASSWORD", default="Admin12345"),
    dict(username="analyst", role="Quality Analyst", full_name="Quality Analyst", employee_id="EMP002",
         department="Quality Control", env="SEED_ANALYST_PASSWORD", default="Analyst12345"),
    dict(username="technician", role="Lab Technician", full_name="Lab Technician", employee_id="EMP003",
         department="Laboratory", env="SEED_TECHNICIAN_PASSWORD", default="Technician12345"),
]


def main():
    app = create_app()
    with app.app_context():
        for s in STARTERS:
            if User.query.filter_by(username=s["username"]).first():
                print(f"- {s['username']}: already exists, skipped")
                continue
            create_user({**{k: v for k, v in s.items() if k not in ("env", "default")},
                         "password": os.getenv(s["env"], s["default"])})
            print(f"+ {s['username']} ({s['role']}): created")
        if "--demo" in sys.argv:
            print(f"Demo data: {seed_demo()} new row(s) added")


if __name__ == "__main__":
    main()
