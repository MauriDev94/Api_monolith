.PHONY: up down logs shell test test-auth migrate

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
