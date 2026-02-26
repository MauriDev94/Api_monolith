from fastapi import FastAPI

from app.features.auth.presentation.api import v1_router as auth_v1_router
from app.features.users.presentation.api import v1_router as users_v1_router

app = FastAPI()

app.include_router(auth_v1_router, tags=["v1 Auth"], prefix="/auth")
app.include_router(users_v1_router, tags=["v1 Users"])


@app.get("/")
def read_root():
    return {"status": "success", "message": "API is running"}
