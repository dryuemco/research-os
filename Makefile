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
	$(PYTHON) -m app.scripts.seed_dev_data --confirm

seed-dev-reset:
	$(PYTHON) -m app.scripts.seed_dev_data --confirm --reset

run-worker:
	$(PYTHON) -m app.scripts.run_execution_worker

run-ops:
	$(PYTHON) -m app.scripts.run_operational_loop

validate-deploy:
	test -f render.yaml
	test -f docs/index.html
	test -f docs/app.js
	test -f docs/js/config.js
	test -f docs/js/api-client.js
	test -f docs/js/ui.js
	test -f docs/js/pages.js
	test -f docs/styles.css
	test -f docs/site-config.example.js
	test -f docs/.nojekyll

check:
	ruff check . && pytest -q
