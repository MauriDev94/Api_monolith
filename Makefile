.PHONY: up down logs shell test test-auth migrate lint format check-format hooks-install hooks-run

up:
	docker compose -f docker-compose-dev.yaml up --build

down:
	docker compose -f docker-compose-dev.yaml down

logs:
	docker compose -f docker-compose-dev.yaml logs -f api

shell:
	docker compose -f docker-compose-dev.yaml exec api sh

test:
	PYTHONPATH=. .venv/bin/pytest -q

test-auth:
	PYTHONPATH=. .venv/bin/pytest tests/features/auth -q

migrate:
	.venv/bin/alembic upgrade head

lint:
	.venv/bin/ruff check app tests

format:
	.venv/bin/ruff check app tests --fix
	.venv/bin/black app tests

check-format:
	.venv/bin/black --check app tests

hooks-install:
	.venv/bin/pre-commit install

hooks-run:
	.venv/bin/pre-commit run --all-files
