# Monolith API (Clean Architecture + DDD)

API monolítica en FastAPI con arquitectura por capas y por feature:

- `domain`: entidades y reglas puras
- `application`: casos de uso y contratos
- `infrastructure`: ORM/repositorios/implementaciones
- `presentation`: endpoints/schemas/mappers
- `di`: wiring de dependencias

## Features actuales

- Auth: register, login, refresh, me
- Users: listado, detalle, actualización, eliminación
- Todos: CRUD protegido por usuario autenticado

## Requisitos

- Python 3.12+ (recomendado)
- Docker (opcional, para Postgres local)

## Configuración rápida

### 1) Crear y activar entorno virtual

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2) Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3) Configurar variables de entorno

Crear archivo `.env` en la raíz con:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=monolith
DB_PORT=5438
DB_HOST=localhost
JWT_SECRET_KEY=super-secret-key
```

Nota: la app usa `EnvConfig` con estos campos: `db_user`, `db_password`, `db_name`, `db_port`, `db_host`, `jwt_secret_key`.

## Base de datos (Postgres con Docker)

Levantar Postgres:

```bash
docker-compose -f docker-compose-dev.yaml --env-file .env up -d
```

Si el puerto está ocupado, cambia `DB_PORT` en `.env` y en `docker-compose-dev.yaml`.

## Migraciones (Alembic)

Aplicar migraciones:

```bash
alembic upgrade head
```

Crear nueva migración:

```bash
alembic revision --autogenerate -m "your message"
```

Comandos útiles:

```bash
alembic current
alembic history --verbose
alembic downgrade -1
alembic downgrade <revision_id>
alembic downgrade base
```

## Ejecutar aplicación

```bash
uvicorn app.main:app --reload
```

- Health check: `GET /`
- Swagger: `http://127.0.0.1:8000/docs`

## Endpoints disponibles

### Auth (`/auth/v1`)

- `POST /auth/v1/register`
- `POST /auth/v1/login`
- `POST /auth/v1/refresh`
- `GET /auth/v1/me`

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

## Flujo recomendado de uso

1. Registrar usuario en `/auth/v1/register`.
2. Loguear en `/auth/v1/login` para obtener `access_token` y `refresh_token`.
3. Consumir endpoints protegidos enviando header:
   - `Authorization: Bearer <access_token>`
4. Renovar access token en `/auth/v1/refresh` con `refresh_token`.

## Testing

La suite está clasificada con marcadores `pytest`:

- `unit`
- `integration`
- `e2e`

### Ejecutar toda la suite

```bash
pytest -q
```

### Ejecutar por tipo

```bash
pytest -q -m unit
pytest -q -m integration
pytest -q -m e2e
```

### Estado actual

- Suite completa pasando
- Cobertura de dominio, casos de uso, repositorios, capa API y flujo E2E principal

## Logging y errores

- Logging configurado con `loguru`.
- Middleware de `request_id` para correlación.
- Handlers globales de excepciones en `app/core/exceptions/error_handling.py`.

## Estructura de tests

- `tests/features/**/domain`: unitarios de dominio
- `tests/features/**/application/usecases`: unitarios de casos de uso
- `tests/features/**/infrastructure/repositories`: integración con DB en memoria
- `tests/features/**/presentation`: integración de capa API con overrides
- `tests/e2e`: flujos end-to-end
