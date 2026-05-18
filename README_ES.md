# Monolith API

API REST lista para producción construida con **FastAPI**, **Clean Architecture** y **Domain-Driven Design** — desplegada en Render con PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green)](https://fastapi.tiangolo.com/)
[![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen)]()
[![Deploy](https://img.shields.io/badge/Deploy-Render-purple)](https://api-monolith.onrender.com)

**API en vivo:** https://api-monolith.onrender.com/docs

---

## Qué demuestra este proyecto

- Monolito modular organizado por feature con arquitectura estricta por capas
- Separación limpia entre lógica de dominio, casos de uso de aplicación e infraestructura
- Autenticación JWT con rotación de refresh token y revocación
- Integración Google OAuth2 SSO
- Restablecimiento de contraseña basado en OTP por email (Resend)
- Logging estructurado con trazabilidad por request (`X-Request-ID`)
- Manejo global de excepciones con respuestas HTTP consistentes
- Pirámide de tests: unit → integración → E2E (92% coverage)

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Migraciones | Alembic |
| Base de datos | PostgreSQL |
| Auth | JWT (PyJWT) + Google OAuth2 |
| Hashing de contraseñas | Argon2 |
| Email | Resend API |
| Logging | Loguru |
| Testing | pytest + pytest-cov |
| Linting | Ruff + Black |
| Deploy | Render (Docker) |

---

## Arquitectura

Este proyecto sigue **Clean Architecture** con **patrones tácticos de DDD**. Cada feature es autocontenida con la misma estructura interna:

```
app/features/<feature>/
├── domain/          # Entidades, value objects, reglas de negocio
├── application/     # Casos de uso, puertos (contratos), DTOs
├── infrastructure/  # Repositorios, proveedores externos
├── presentation/    # Routers FastAPI, schemas, mappers
└── di/              # Wiring de dependencias
```

**Regla de dependencia:** las capas externas dependen de las internas, nunca al revés. El dominio no tiene dependencias de frameworks.

Para detalles arquitectónicos completos, decisiones y diagramas → [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Features

### Auth
- `POST /auth/v1/register` — registrarse con email/contraseña
- `POST /auth/v1/login` — iniciar sesión, retorna access + refresh tokens
- `POST /auth/v1/refresh` — rotar refresh token
- `GET  /auth/v1/me` — usuario autenticado actual
- `POST /auth/v1/request-otp` — solicitar OTP para restablecer contraseña
- `POST /auth/v1/change-password` — cambiar contraseña con OTP
- `GET  /auth/v1/google` — iniciar Google SSO
- `GET  /auth/v1/google/callback` — completar Google SSO, retorna tokens
- `POST /auth/v1/link-google` — vincular cuenta Google a usuario existente

### Users
- `GET    /v1/users` — listar todos los usuarios
- `GET    /v1/users/{id}` — obtener usuario por id (solo propio)
- `PUT    /v1/users/{id}` — actualizar perfil (solo propio)
- `DELETE /v1/users/{id}` — eliminar cuenta (solo propio)

### Todos
- `POST   /v1/todos` — crear tarea
- `GET    /v1/todos` — listar tareas (filtradas por usuario autenticado)
- `GET    /v1/todos/{id}` — obtener tarea por id (con control de ownership)
- `PUT    /v1/todos/{id}` — actualizar tarea
- `DELETE /v1/todos/{id}` — eliminar tarea

### Notifications
- `GET   /v1/notifications` — listar notificaciones del usuario autenticado
- `PATCH /v1/notifications/{id}/read` — marcar notificación como leída

---

## Decisiones Clave de Diseño

**Manejadores globales de excepción en vez de try/except en endpoints** — los errores de negocio se lanzan en la capa de dominio/aplicación y son capturados por handlers registrados en `core/exceptions/error_handling.py`. Los endpoints se mantienen limpios.

**Puertos y adaptadores por feature** — cada feature define sus propios contratos (`application/contracts/`) para que las implementaciones de infraestructura sean intercambiables sin tocar la lógica de negocio.

**Rotación de refresh token con revocación** — cada refresh emite un nuevo par de tokens y revoca el JTI anterior. La reutilización de un token revocado invalida todos los tokens activos de ese usuario.

**Value Object Email** — validación por regex compatible con RFC en el dominio, no en la capa de transporte. La normalización (minúsculas, trim) ocurre en la construcción.

**Google SSO retorna JSON, no redirect** — `GET /auth/v1/google` retorna `{ authorization_url }` para que el frontend decida cómo navegar, manteniendo el backend sin estado.

---

## Ejecución Local

**Requisitos:** Python 3.12, Docker

```bash
# Clonar
git clone https://github.com/MauriDev94/Api_monolith.git
cd Api_monolith

# Entorno
cp .env.example .env
# Completar DB_USER, DB_PASSWORD, DB_NAME, DB_PORT, JWT_SECRET_KEY

# Iniciar DB
docker compose -f docker-compose-dev.yaml up db -d

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
alembic upgrade head

# Iniciar API
uvicorn app.main:app --reload
```

API disponible en `http://localhost:8000/docs`

---

## Ejecutar Tests

```bash
# Todos los tests
pytest

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing -q

# Por tipo
pytest -m unit
pytest -m integration
pytest -m e2e
```

---

## Variables de Entorno

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

Ver `.env.example` para referencia completa.

---

## Estructura del Proyecto

```
app/
├── main.py                   # Bootstrap, middlewares, registro de routers
├── common/                   # Contratos base de casos de uso compartidos
├── core/                     # Transversal: config, DB, excepciones, middlewares
└── features/
    ├── auth/                 # Autenticación, JWT, OTP, Google SSO
    ├── users/                # Gestión de perfil de usuario
    ├── todos/                # CRUD de tareas con control de ownership
    └── notifications/        # Notificaciones de recordatorios

tests/
├── core/                     # Tests de manejo de excepciones del core
├── features/                 # Tests unitarios + de integración por feature
└── e2e/                      # Tests de flujo completo con DB real (SQLite in-memory)
```

---

## Autor

**Mauricio** — Python Backend Developer
Construyendo hacia nivel mid-level con enfoque en clean architecture, DDD y código listo para producción.

[GitHub](https://github.com/MauriDev94) · [API Docs](https://api-monolith.onrender.com/docs)
