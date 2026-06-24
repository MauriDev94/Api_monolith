import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic_settings import BaseSettings
from sqlalchemy import text

from app.core.config.logger_config import setup_logger
from app.core.exceptions.error_handling import register_exception_handlers
from app.core.middleware.rate_limit_global import GlobalRateLimitMiddleware
from app.core.middleware.request_context import attach_request_id_middleware
from app.core.middleware.security_headers import attach_security_headers
from app.features.auth.presentation.api import v1_router as auth_v1_router
from app.features.notifications.presentation.api import v1_router as notifications_v1_router
from app.features.todos.presentation.api import v1_router as todos_v1_router
from app.features.users.presentation.api import v1_router as users_v1_router


class AppSettings(BaseSettings):
    """Application settings from environment."""

    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Apply Alembic migrations on startup when running in production."""
    from alembic import command
    from alembic.config import Config

    app_env = os.getenv("APP_ENV", "dev")
    if app_env == "production":
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic migrations applied successfully")
        except Exception as e:
            logger.error(f"Failed to apply migrations: {e}")
            # Fail-fast: no servir tráfico contra un esquema roto/desactualizado.
            # En Render free no hay shell ni migración manual → el startup es el único
            # camino; dejar morir el proceso para que la plataforma reintente/avise.
            raise
    yield


settings = AppSettings()
setup_logger()
app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Internal-Token"],
)

# Global per-IP rate limiting. Se registra ANTES de los middlewares de headers/contexto
# para que estos queden por FUERA: así un 429 del limiter igual sale con security headers
# y request id (antes el 429 del limiter global se los saltaba). Gateado por env para que
# la suite de tests (RATE_LIMIT_ENABLED=false) no acumule estado entre tests que comparten
# la IP del TestClient.
if os.getenv("RATE_LIMIT_ENABLED", "true").lower() != "false":
    app.add_middleware(GlobalRateLimitMiddleware)

# Security headers middleware (por fuera del rate limiter → aplica también a los 429)
app.middleware("http")(attach_security_headers)

# Request context middleware
app.middleware("http")(attach_request_id_middleware)

# Auth endpoints include register/login/refresh/me.
app.include_router(auth_v1_router, tags=["v1 Auth"], prefix="/auth")
# User endpoints are protected and require bearer authentication.
app.include_router(users_v1_router, tags=["v1 Users"])
# Todo endpoints are protected and scoped by authenticated user ownership.
app.include_router(todos_v1_router, tags=["v1 Todos"])
# Notification endpoints for user alerts and reminders.
app.include_router(notifications_v1_router, tags=["v1 Notifications"])


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="MauriDev Portfolio API",
        version="1.0.0",
        description="REST API para gestión de TODOs con autenticación JWT. "
        "Construida con FastAPI + Clean Architecture + DDD.",
        routes=app.routes,
        contact={
            "name": "MauriDev",
            "url": "https://github.com/MauriDev94",
            "email": "mauridev94@gmail.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )
    security_schemes = openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    openapi_schema.setdefault("security", []).append({"BearerAuth": []})

    PUBLIC_PATHS = {
        "/auth/v1/register",
        "/auth/v1/login",
        "/auth/v1/refresh",
        "/",
        "/health",
    }
    for path, path_item in openapi_schema.get("paths", {}).items():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            if path in PUBLIC_PATHS:
                operation["security"] = []  # override explícito: sin auth
                continue
            security = operation.get("security")
            if security is None:
                operation["security"] = [{"BearerAuth": []}]
                continue
            if all("BearerAuth" not in item for item in security):
                security.append({"BearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.get("/")
def read_root():
    """Basic liveness endpoint for local smoke checks."""
    return {"status": "success", "message": "API is running"}


@app.get("/health")
def health_check():
    """Readiness check: responde 503 si la DB no responde. Liveness puro es `/`."""
    from app.core.providers.db import get_db_session

    db_healthy = True
    db_gen = None
    try:
        db_gen = get_db_session()
        db_session = next(db_gen)
        db_session.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False
    finally:
        if db_gen is not None:
            db_gen.close()

    if not db_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "unhealthy"},
        )
    return {"status": "healthy", "database": "healthy"}
