PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e .[dev]

run:
	uvicorn app.main:app --reload

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
