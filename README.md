# Monolith API

A production-ready REST API built with **FastAPI**, **Clean Architecture**, and **Domain-Driven Design** — deployed on Render with PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green)](https://fastapi.tiangolo.com/)
[![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen)]()
[![Deploy](https://img.shields.io/badge/Deploy-Render-purple)](https://api-monolith.onrender.com)

**Live API:** https://api-monolith.onrender.com/docs

---

## What this project demonstrates

- Modular monolith organized by feature with strict layered architecture
- Clean separation between domain logic, application use cases, and infrastructure
- JWT authentication with refresh token rotation and revocation
- Google OAuth2 SSO integration
- OTP-based password reset via email (Resend)
- Structured logging with request tracing (`X-Request-ID`)
- Global exception handling with consistent HTTP responses
- Test pyramid: unit → integration → E2E (92% coverage)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database | PostgreSQL |
| Auth | JWT (PyJWT) + Google OAuth2 |
| Password hashing | Argon2 |
| Email | Resend API |
| Logging | Loguru |
| Testing | pytest + pytest-cov |
| Linting | Ruff + Black |
| Deploy | Render (Docker) |

---

## Architecture

This project follows **Clean Architecture** with **DDD tactical patterns**. Each feature is self-contained with the same internal structure:

```
app/features/<feature>/
├── domain/          # Entities, value objects, business rules
├── application/     # Use cases, ports (contracts), DTOs
├── infrastructure/  # Repositories, external providers
├── presentation/    # FastAPI routers, schemas, mappers
└── di/              # Dependency wiring
```

**Dependency rule:** outer layers depend on inner layers, never the reverse. Domain has zero framework dependencies.

For full architectural details, decisions, and diagrams → [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Features

### Auth
- `POST /auth/v1/register` — register with email/password
- `POST /auth/v1/login` — login, returns access + refresh tokens
- `POST /auth/v1/refresh` — rotate refresh token
- `GET  /auth/v1/me` — current authenticated user
- `POST /auth/v1/request-otp` — request OTP for password reset
- `POST /auth/v1/change-password` — change password with OTP
- `GET  /auth/v1/google` — initiate Google SSO
- `GET  /auth/v1/google/callback` — complete Google SSO, returns tokens
- `POST /auth/v1/link-google` — link Google account to existing user

### Users
- `GET    /v1/users` — list all users
- `GET    /v1/users/{id}` — get user by id (self only)
- `PUT    /v1/users/{id}` — update profile (self only)
- `DELETE /v1/users/{id}` — delete account (self only)

### Todos
- `POST   /v1/todos` — create todo
- `GET    /v1/todos` — list todos (scoped to authenticated user)
- `GET    /v1/todos/{id}` — get todo by id (ownership enforced)
- `PUT    /v1/todos/{id}` — update todo
- `DELETE /v1/todos/{id}` — delete todo

### Notifications
- `GET   /v1/notifications` — list notifications for authenticated user
- `PATCH /v1/notifications/{id}/read` — mark notification as read

---

## Key Design Decisions

**Global exception handlers over try/except in endpoints** — business errors are raised in the domain/application layer and caught by registered handlers in `core/exceptions/error_handling.py`. Endpoints stay clean.

**Ports and adapters per feature** — each feature defines its own contracts (`application/contracts/`) so infrastructure implementations are swappable without touching business logic.

**Refresh token rotation with revocation** — every refresh issues a new token pair and revokes the previous JTI. Reuse of a revoked token revokes all active tokens for that user.

**Email Value Object** — RFC-compliant regex validation in the domain, not in the transport layer. Normalization (lowercase, trim) happens at construction.

**Google SSO returns JSON, not redirect** — `GET /auth/v1/google` returns `{ authorization_url }` so the frontend decides how to navigate, keeping the backend stateless.

---

## Running Locally

**Requirements:** Python 3.12, Docker

```bash
# Clone
git clone https://github.com/MauriDev94/Api_monolith.git
cd Api_monolith

# Environment
cp .env.example .env
# Fill in DB_USER, DB_PASSWORD, DB_NAME, DB_PORT, JWT_SECRET_KEY

# Start DB
docker compose -f docker-compose-dev.yaml up db -d

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload
```

API available at `http://localhost:8000/docs`

---

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing -q

# By type
pytest -m unit
pytest -m integration
pytest -m e2e
```

---

## Environment Variables

```env
DB_USER=
DB_PASSWORD=
DB_NAME=
DB_PORT=5432
DB_HOST=localhost
JWT_SECRET_KEY=

# Email (Resend)
RESEND_API_KEY=
RESEND_SENDER_EMAIL=

# Google OAuth2
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/v1/google/callback
```

See `.env.example` for full reference.

---

## Project Structure

```
app/
├── main.py                   # Bootstrap, middleware, router registration
├── common/                   # Shared use case base contracts
├── core/                     # Cross-cutting: config, DB, exceptions, middleware
└── features/
    ├── auth/                 # Authentication, JWT, OTP, Google SSO
    ├── users/                # User profile management
    ├── todos/                # Todo CRUD with ownership control
    └── notifications/        # Reminder notifications

tests/
├── core/                     # Core exception handling tests
├── features/                 # Unit + integration tests per feature
└── e2e/                      # Full flow tests with real DB (SQLite in-memory)
```

---

## Author

**Mauricio** — Python Backend Developer
Building toward mid-level with a focus on clean architecture, DDD, and production-ready code.

[GitHub](https://github.com/MauriDev94) · [API Docs](https://api-monolith.onrender.com/docs)
