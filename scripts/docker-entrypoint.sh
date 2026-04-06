#!/usr/bin/env sh
set -eu

echo "[entrypoint] Running migrations: alembic upgrade head"
alembic upgrade head

echo "[entrypoint] Starting app: python -m app.main"
exec python -m app.main
