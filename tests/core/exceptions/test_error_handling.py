from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.exceptions.error_handling import register_exception_handlers
from app.core.exceptions.exceptions import (
    DatabaseException,
    InternalServerErrorException,
    InvalidCredentialsException,
    ResourceConflictException,
    ResourceNotFoundException,
)


class ValidationPayload(BaseModel):
    name: str = Field(min_length=2)


def create_test_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/validation")
    def validation_endpoint(payload: ValidationPayload) -> dict[str, str]:
        return {"name": payload.name}

    @app.get("/invalid-credentials")
    def invalid_credentials() -> None:
        raise InvalidCredentialsException()

    @app.get("/resource-conflict")
    def resource_conflict() -> None:
        raise ResourceConflictException("email already registered")

    @app.get("/resource-not-found")
    def resource_not_found() -> None:
        raise ResourceNotFoundException("user not found")

    @app.get("/database-error")
    def database_error() -> None:
        raise DatabaseException("db offline")

    @app.get("/internal-error")
    def internal_error() -> None:
        raise InternalServerErrorException("unexpected")

    @app.get("/http-404")
    def http_404() -> None:
        raise HTTPException(status_code=404, detail="custom missing")

    @app.get("/http-500")
    def http_500() -> None:
        raise HTTPException(status_code=500, detail="sensitive detail")

    @app.get("/generic-error")
    def generic_error() -> None:
        raise RuntimeError("boom")

    return TestClient(app, raise_server_exceptions=False)


def test_should_return_400_when_validation_fails() -> None:
    client = create_test_client()

    response = client.post("/validation", json={"name": "x"})

    assert response.status_code == 400
    assert response.json()["message"] == "Validation error"


def test_should_return_401_for_invalid_credentials_exception() -> None:
    client = create_test_client()

    response = client.get("/invalid-credentials")

    assert response.status_code == 401
    assert response.json() == {"message": "Invalid email or password"}


def test_should_return_409_for_resource_conflict_exception() -> None:
    client = create_test_client()

    response = client.get("/resource-conflict")

    assert response.status_code == 409
    assert response.json()["message"] == "email already registered"


def test_should_return_404_for_resource_not_found_exception() -> None:
    client = create_test_client()

    response = client.get("/resource-not-found")

    assert response.status_code == 404
    assert response.json()["message"] == "user not found"


def test_should_return_500_for_database_exception() -> None:
    client = create_test_client()

    response = client.get("/database-error")

    assert response.status_code == 500
    assert response.json()["message"] == "Database error occurred"


def test_should_return_500_for_internal_server_error_exception() -> None:
    client = create_test_client()

    response = client.get("/internal-error")

    assert response.status_code == 500
    assert response.json()["message"] == "Internal server error"


def test_should_keep_http_404_detail() -> None:
    client = create_test_client()

    response = client.get("/http-404")

    assert response.status_code == 404
    assert response.json() == {"message": "custom missing"}


def test_should_mask_http_500_detail() -> None:
    client = create_test_client()

    response = client.get("/http-500")

    assert response.status_code == 500
    assert response.json()["message"] == "Internal server error"
    assert "unexpected error occurred" in response.json()["detail"].lower()


def test_should_return_500_for_unhandled_exceptions() -> None:
    client = create_test_client()

    response = client.get("/generic-error")

    assert response.status_code == 500
    assert response.json()["message"] == "Internal server error"

