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
.\scripts\dev.ps1 down
```

### Makefile (Linux/macOS)

```bash
make up
make logs
make migrate
make test
make test-auth
make down
```

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

- `69` tests pasando (`features/auth` + e2e relevantes)

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

- Dockerizar app completa (`Dockerfile` + `docker-compose` app+db).
- CI con GitHub Actions (tests + migraciones).
- CD básico a entorno de deploy.
- Observabilidad mínima (health, logs, métricas).
