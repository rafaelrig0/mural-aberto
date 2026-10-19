.PHONY: install test-db test lint format typecheck migrate run

install:
	pip install -r requirements-dev.txt

test-db:
	docker compose up -d test-db

test:
	pytest

lint:
	ruff check . && ruff format --check .

format:
	ruff check --fix . && ruff format .

typecheck:
	mypy app

migrate:
	alembic upgrade head

run:
	uvicorn app.main:app --reload
