#!/usr/bin/env sh
set -eu

cd /workspace
export PYTHONPATH="/workspace:${PYTHONPATH:-}"

echo "[entrypoint] Repairing alembic_version table/column before migrations"
python - <<'PY'
from sqlalchemy import create_engine, text

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.sqlalchemy_database_url(), future=True)

with engine.begin() as conn:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(255) NOT NULL PRIMARY KEY
            )
            """
        )
    )
    conn.execute(
        text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
    )
PY

echo "[entrypoint] Running migrations: alembic upgrade head"
python -m alembic -c /workspace/alembic.ini upgrade head

echo "[entrypoint] Starting app: python -m app.main"
exec python -m app.main
