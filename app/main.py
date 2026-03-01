from fastapi import FastAPI

from app.core.exceptions.error_handling import register_exception_handlers
from app.features.auth.presentation.api import v1_router as auth_v1_router
from app.features.users.presentation.api import v1_router as users_v1_router

app = FastAPI()
register_exception_handlers(app)

# Auth endpoints include register/login/refresh/me.
app.include_router(auth_v1_router, tags=["v1 Auth"], prefix="/auth")
# User endpoints are protected and require bearer authentication.
app.include_router(users_v1_router, tags=["v1 Users"])


@app.get("/")
def read_root():
    """Basic liveness endpoint for local smoke checks."""
    return {"status": "success", "message": "API is running"}
