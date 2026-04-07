from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.identity_models import User
from app.security.passwords import verify_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def authenticate(self, *, username: str, password: str) -> User | None:
        user = self.db.scalar(select(User).where(User.username == username))
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
