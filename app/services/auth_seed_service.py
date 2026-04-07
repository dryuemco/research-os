from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.common.enums import UserRole
from app.domain.identity_models import User
from app.security.passwords import hash_password


class AuthSeedService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def ensure_seed_admin_users(self) -> int:
        created = 0
        for username, full_name, password, email in (
            ("admin1", "Seeded Admin 1", self.settings.seed_admin1_password, "admin1@local.invalid"),
            ("admin2", "Seeded Admin 2", self.settings.seed_admin2_password, "admin2@local.invalid"),
        ):
            user = self.db.scalar(select(User).where(User.username == username))
            if user is not None:
                continue
            self.db.add(
                User(
                    username=username,
                    password_hash=hash_password(password),
                    full_name=full_name,
                    email=email,
                    role=UserRole.ADMIN,
                    is_active=True,
                    display_name=full_name,
                )
            )
            created += 1
        self.db.flush()
        return created
