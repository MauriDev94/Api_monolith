.PHONY: up down logs shell test test-auth migrate lint format check-format check hooks-install hooks-run

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
	.venv/bin/ruff format app tests
	.venv/bin/ruff check app tests --fix

check-format:
	.venv/bin/ruff format --check app tests

# Gate unico. Delega en harness verify, NO re-declara los comandos.
# --when push corre format + lint + types + tests; deja tests-full para CI
# porque necesita Docker (testcontainers levanta Postgres con pgvector).
check:
	python .harness/verify.py --root . --when push

hooks-install:
	.venv/bin/pre-commit install

hooks-run:
	.venv/bin/pre-commit run --all-files
