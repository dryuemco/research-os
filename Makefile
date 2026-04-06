PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e .[dev]

run:
	uvicorn app.main:app --reload

run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest

lint:
	ruff check .

format-check:
	ruff format --check .

migrate:
	alembic upgrade head

makemigration:
	alembic revision --autogenerate -m "$(m)"

seed-dev:
	$(PYTHON) -m app.scripts.seed_dev_data

run-worker:
	$(PYTHON) -m app.scripts.run_execution_worker

run-ops:
	$(PYTHON) -m app.scripts.run_operational_loop

validate-deploy:
	test -f render.yaml
	test -f pages/index.html
	test -f .github/workflows/deploy-pages.yml

check:
	ruff check . && pytest -q
