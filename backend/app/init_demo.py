from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.infrastructure.db import SessionLocal
from app.models.entities import User


def main() -> None:
    accounts = {
        "demo_user": ("user", "DEMO_USER_PASSWORD"),
        "demo_legal": ("legalReviewer", "DEMO_LEGAL_REVIEWER_PASSWORD"),
        "demo_risk": ("riskReviewer", "DEMO_RISK_REVIEWER_PASSWORD"),
        "demo_admin": ("admin", "DEMO_ADMIN_PASSWORD"),
    }
    db = SessionLocal()
    try:
        for username, (role, password_var) in accounts.items():
            password = os.getenv(password_var)
            if not password:
                raise SystemExit(f"{password_var} is required")
            user = db.scalar(select(User).where(User.username == username))
            if user:
                user.role, user.status, user.password_hash = role, "active", hash_password(password)
            else:
                db.add(
                    User(
                        username=username,
                        role=role,
                        status="active",
                        password_hash=hash_password(password),
                    )
                )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
