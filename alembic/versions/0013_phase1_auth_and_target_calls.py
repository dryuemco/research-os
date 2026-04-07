"""phase1 auth and target calls

Revision ID: 0013_phase1_auth_and_target_calls
Revises: 0012_repair_operational_tables_if_missing
Create Date: 2026-04-07 00:00:00
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = "0013_phase1_auth_and_target_calls"
down_revision = "0012_repair_operational_tables_if_missing"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    return column_name in columns


def _hash_password(password: str) -> str:
    iterations = 390000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return (
        "pbkdf2_sha256"
        f"${iterations}"
        f"${base64.urlsafe_b64encode(salt).decode('utf-8')}"
        f"${base64.urlsafe_b64encode(digest).decode('utf-8')}"
    )


def upgrade() -> None:
    if not _has_column("users", "username"):
        op.add_column("users", sa.Column("username", sa.String(length=255), nullable=True))
    if not _has_column("users", "password_hash"):
        op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    if not _has_column("users", "full_name"):
        op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))

    op.execute("UPDATE users SET username = COALESCE(username, email)")
    op.execute(
        "UPDATE users SET password_hash = COALESCE(password_hash, 'disabled-migrated-account')"
    )

    if not _has_column("users", "email"):
        op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    if not _has_column("users", "display_name"):
        op.add_column("users", sa.Column("display_name", sa.String(length=255), nullable=True))

    op.alter_column("users", "username", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("users", "password_hash", existing_type=sa.Text(), nullable=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    if not _has_table("target_calls"):
        op.create_table(
            "target_calls",
            sa.Column("title", sa.String(length=512), nullable=False),
            sa.Column("programme", sa.String(length=128), nullable=False),
            sa.Column("call_url", sa.String(length=1024), nullable=True),
            sa.Column("call_identifier", sa.String(length=255), nullable=True),
            sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("raw_call_text", sa.Text(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("created_by_user_id", sa.String(), nullable=False),
            sa.Column("id", sa.String(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_target_calls_programme"), "target_calls", ["programme"], unique=False)
        op.create_index(op.f("ix_target_calls_status"), "target_calls", ["status"], unique=False)
        op.create_index(
            op.f("ix_target_calls_created_by_user_id"),
            "target_calls",
            ["created_by_user_id"],
            unique=False,
        )

    admin1_password = os.getenv("SEED_ADMIN1_PASSWORD", "dev-admin1-placeholder-change-me")
    admin2_password = os.getenv("SEED_ADMIN2_PASSWORD", "dev-admin2-placeholder-change-me")

    now = datetime.now(timezone.utc)
    users_table = sa.table(
        "users",
        sa.column("id", sa.String()),
        sa.column("username", sa.String()),
        sa.column("password_hash", sa.Text()),
        sa.column("full_name", sa.String()),
        sa.column("email", sa.String()),
        sa.column("display_name", sa.String()),
        sa.column("role", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    bind = op.get_bind()
    for username, full_name, password in (
        ("admin1", "Seeded Admin 1", admin1_password),
        ("admin2", "Seeded Admin 2", admin2_password),
    ):
        exists = bind.execute(
            sa.text("SELECT id FROM users WHERE username = :username"), {"username": username}
        ).scalar_one_or_none()
        if exists:
            continue
        op.bulk_insert(
            users_table,
            [
                {
                    "id": str(uuid.uuid4()),
                    "username": username,
                    "password_hash": _hash_password(password),
                    "full_name": full_name,
                    "email": None,
                    "display_name": full_name,
                    "role": "admin",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE username IN ('admin1', 'admin2')")

    if _has_table("target_calls"):
        op.drop_index(op.f("ix_target_calls_created_by_user_id"), table_name="target_calls")
        op.drop_index(op.f("ix_target_calls_status"), table_name="target_calls")
        op.drop_index(op.f("ix_target_calls_programme"), table_name="target_calls")
        op.drop_table("target_calls")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "full_name")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "username")
