from uuid import uuid4

from fastapi import FastAPI, Request
from loguru import logger

from app.core.config.logger_config import setup_logger
from app.core.exceptions.error_handling import register_exception_handlers
from app.features.auth.presentation.api import v1_router as auth_v1_router
from app.features.users.presentation.api import v1_router as users_v1_router

setup_logger()
app = FastAPI()
register_exception_handlers(app)


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    """Attach and propagate request id for tracing across logs and responses."""
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id

    request_logger = logger.bind(request_id=request_id)
    request_logger.info(f"Incoming request {request.method} {request.url.path}")

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    request_logger.info(
        f"Completed request {request.method} {request.url.path} with status {response.status_code}"
    )
    return response


# Auth endpoints include register/login/refresh/me.
app.include_router(auth_v1_router, tags=["v1 Auth"], prefix="/auth")
# User endpoints are protected and require bearer authentication.
app.include_router(users_v1_router, tags=["v1 Users"])


@app.get("/")
def read_root():
    """Basic liveness endpoint for local smoke checks."""
    return {"status": "success", "message": "API is running"}
