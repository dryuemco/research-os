#!/usr/bin/env sh
set -eu

cd /workspace
export PYTHONPATH="/workspace:${PYTHONPATH:-}"

echo "[entrypoint] Running migrations: alembic upgrade head"
python -m alembic -c /workspace/alembic.ini upgrade head

echo "[entrypoint] Starting app: python -m app.main"
exec python -m app.main
