from fastapi import FastAPI

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


@app.get("/")
def read_root():
    """Basic liveness endpoint for local smoke checks."""
    return {"status": "success", "message": "API is running"}
