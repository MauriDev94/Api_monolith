# Monolith API (FastAPI + Clean Architecture + DDD)

Proyecto backend modular en FastAPI orientado a portafolio profesional.

Arquitectura por feature y por capas:

- `domain`: entidades, value objects, reglas de negocio.
- `application`: casos de uso, contratos (ports), DTOs.
- `infrastructure`: repositorios SQLAlchemy, providers, implementaciones técnicas.
- `presentation`: endpoints, schemas HTTP, mappers.
- `di`: wiring de dependencias por feature.

---

## Estado actual del proyecto

Features implementadas:

- `Auth`
  - `register`, `login`, `refresh`, `me`
  - OTP por email para cambio de contraseña
  - `change-password` con OTP (flujo recomendado)
  - `verify-otp` marcado como **deprecated** (compatibilidad legacy)
  - refresh token rotation + revocación
  - rate limiting en endpoints sensibles de OTP
- `Users`
  - listar, detalle, actualizar, eliminar
- `Todos`
  - CRUD protegido por usuario autenticado

Hardening de seguridad ya aplicado:

- OTP ligado al usuario autenticado (no se recibe `user_id` por request).
- OTP restringido a propósito `password_change`.
- OTP almacenado hasheado en DB (`code_hash`), no en texto plano.
- Excepciones globales mapeadas a HTTP (`401`, `404`, `409`, `422`, `429`, `500`).

---

## Requisitos

- Python 3.12+
- PostgreSQL (local o Docker)
- Docker (opcional, recomendado para entorno local rápido)

---

## Setup local

### 1) Crear entorno virtual

```bash
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2) Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3) Configurar `.env`

Crear `.env` en raíz:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=monolith
DB_PORT=5438
DB_HOST=localhost
JWT_SECRET_KEY=super-secret-key

# Opcional SMTP (OTP real por email)
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_SENDER_EMAIL=
SMTP_USE_TLS=true
```

Si SMTP no está configurado, se usa sender de consola para desarrollo.

---

## Base de datos

Levantar PostgreSQL con Docker:

```bash
docker-compose -f docker-compose-dev.yaml --env-file .env up -d
```

Aplicar migraciones:

```bash
alembic upgrade head
```

Comandos útiles:

```bash
alembic current
alembic history --verbose
alembic downgrade -1
```

---

## Ejecutar la API

```bash
uvicorn app.main:app --reload
```

- Health check: `GET /`
- Swagger: `http://127.0.0.1:8000/docs`

---

## Comandos de desarrollo

### PowerShell (Windows)

```powershell
.\scripts\dev.ps1 up
.\scripts\dev.ps1 logs
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 test
.\scripts\dev.ps1 test-auth
.\scripts\dev.ps1 lint
.\scripts\dev.ps1 format
.\scripts\dev.ps1 check-format
.\scripts\dev.ps1 hooks-install
.\scripts\dev.ps1 hooks-run
.\scripts\dev.ps1 down
```

### Makefile (Linux/macOS)

```bash
make up
make logs
make migrate
make test
make test-auth
make lint
make format
make check-format
make hooks-install
make hooks-run
make down
```

---

## Hooks automáticos (pre-commit)

Este proyecto usa hooks de `pre-commit` para ejecutar validaciones antes de cada commit.

Incluye:

- `check-merge-conflict`
- `end-of-file-fixer`
- `trailing-whitespace`
- `ruff --fix`
- `black`

Instalación local:

```powershell
.\scripts\dev.ps1 hooks-install
```

Ejecución manual sobre todo el repo:

```powershell
.\scripts\dev.ps1 hooks-run
```

Después de instalar, cada `git commit` ejecutará los hooks automáticamente.

---

## CI (GitHub Actions)

Workflow activo:

- `.github/workflows/tests.yml`
- Se ejecuta en `push` y `pull_request` contra `main`.
- Jobs:
  - `quality`: `ruff` (gate inicial enfocado en errores críticos `E,F,B`)
  - `tests`: `pytest` + cobertura (`--cov=app`) con mínimo `70%`

Secrets requeridos en el repositorio:

- `CI_DB_PASSWORD`
- `CI_JWT_SECRET_KEY`

Notas:

- El job de CI genera un `.env` efímero antes de `pytest -q`.
- No se versionan credenciales reales en el repo.
- Se publica `coverage.xml` como artifact del workflow.
- La política de lint está en modo incremental para no bloquear por deuda histórica de estilo.

---

## Endpoints principales

### Auth (`/auth/v1`)

- `POST /auth/v1/register`
- `POST /auth/v1/login`
- `POST /auth/v1/refresh`
- `GET /auth/v1/me`
- `POST /auth/v1/request-otp`
- `POST /auth/v1/change-password`  **(flujo recomendado)**
- `POST /auth/v1/verify-otp`  **(deprecated)**

### Users (`/v1`)

- `GET /v1/users`
- `GET /v1/users/{user_id}`
- `PUT /v1/users/{user_id}`
- `DELETE /v1/users/{user_id}`

### Todos (`/v1`)

- `POST /v1/todos`
- `GET /v1/todos`
- `GET /v1/todos/{todo_id}`
- `PUT /v1/todos/{todo_id}`
- `DELETE /v1/todos/{todo_id}`

---

## Flujo recomendado (password change con OTP)

1. Login en `/auth/v1/login`.
2. Solicitar OTP en `/auth/v1/request-otp` con bearer token.
3. Cambiar password en `/auth/v1/change-password` con `code` + `new_password`.
4. Re-login con la nueva contraseña.
5. El OTP no se puede reutilizar.

---

## Testing

Markers:

- `unit`
- `integration`
- `e2e`

Ejecutar todo:

```bash
pytest -q
```

Ejecutar por tipo:

```bash
pytest -q -m unit
pytest -q -m integration
pytest -q -m e2e
```

Ejemplo smoke de auth OTP:

```bash
pytest -q tests/e2e/test_auth_users_todos_e2e.py::test_should_change_password_with_otp_and_reject_reused_code
```

Estado validado recientemente:

- `152` tests pasando (suite completa)

---

## Logging y errores

- Logging con `loguru`.
- Middleware `request_id` para trazabilidad.
- Manejo global de errores en `app/core/exceptions/error_handling.py`.

---

## Estructura del proyecto

```text
app/
├── core/
├── common/
└── features/
    ├── auth/
    ├── users/
    └── todos/
tests/
├── features/
└── e2e/
```

---

## Roadmap corto (siguiente etapa)

- CI extendido: lint + format-check + cobertura.
- CD básico a entorno de deploy.
- Observabilidad mínima (health, logs, métricas).
