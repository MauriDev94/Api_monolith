from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config.logger_config import setup_logger
from app.core.exceptions.error_handling import register_exception_handlers
from app.core.middleware.request_context import attach_request_id_middleware
from app.features.auth.presentation.api import v1_router as auth_v1_router
from app.features.todos.presentation.api import v1_router as todos_v1_router
from app.features.users.presentation.api import v1_router as users_v1_router

setup_logger()
app = FastAPI()
register_exception_handlers(app)
app.middleware("http")(attach_request_id_middleware)

# Auth endpoints include register/login/refresh/me.
app.include_router(auth_v1_router, tags=["v1 Auth"], prefix="/auth")
# User endpoints are protected and require bearer authentication.
app.include_router(users_v1_router, tags=["v1 Users"])
# Todo endpoints are protected and scoped by authenticated user ownership.
app.include_router(todos_v1_router, tags=["v1 Todos"])

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Monolith API",
        version="1.0.0",
        description="API docs",
        routes=app.routes,
    )
    security_schemes = openapi_schema.setdefault("components", {}).setdefault(
        "securitySchemes", {}
    )
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    openapi_schema.setdefault("security", []).append({"BearerAuth": []})

    # Allow BearerAuth alongside existing OAuth2 requirements per operation.
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            security = operation.get("security")
            if security is None:
                operation["security"] = [{"BearerAuth": []}]
                continue
            if all("BearerAuth" not in item for item in security):
                security.append({"BearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


@app.get("/")
def read_root():
    """Basic liveness endpoint for local smoke checks."""
    return {"status": "success", "message": "API is running"}
