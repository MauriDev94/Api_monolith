from fastapi import APIRouter


def get_versioned_router(version: str) -> APIRouter:
    return APIRouter(prefix=f"/{version}")
