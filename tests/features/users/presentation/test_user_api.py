from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions.error_handling import register_exception_handlers
from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.users.di.dependencies import (
    get_delete_user_use_case,
    get_get_all_users_use_case,
    get_get_user_by_id_use_case,
    get_update_user_use_case,
)
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email
from app.features.users.presentation.api import v1_router


class StubUseCase:
    def __init__(self, result=None):
        self.result = result
        self.received = None

    def execute(self, params=None):
        self.received = params
        return self.result


def make_user(user_id: str = "user-1") -> User:
    return User(
        id=user_id,
        name="Mauri",
        lastname="Salinas",
        email=Email("mauri@mail.com"),
        password_hash="hashed-password",
        birthdate=date(2000, 1, 1),
    )


def create_test_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(v1_router)
    return TestClient(app, raise_server_exceptions=False)


def override_all_user_use_cases(client: TestClient, use_case: StubUseCase) -> None:
    app = client.app
    app.dependency_overrides[get_get_all_users_use_case] = lambda: use_case
    app.dependency_overrides[get_get_user_by_id_use_case] = lambda: use_case
    app.dependency_overrides[get_update_user_use_case] = lambda: use_case
    app.dependency_overrides[get_delete_user_use_case] = lambda: use_case


# Tipo de test: Integration
def test_should_return_404_when_get_user_by_id_is_not_self() -> None:
    """Valida que get user by id responde 404 cuando no coincide con el usuario autenticado."""
    client = create_test_client()
    use_case = StubUseCase(result=make_user("other-user"))
    override_all_user_use_cases(client, use_case)
    client.app.dependency_overrides[get_authenticated_user] = lambda: make_user("user-1")

    response = client.get("/v1/users/other-user")

    assert response.status_code == 404
    assert response.json()["message"] == "user not found"
    assert use_case.received is None


# Tipo de test: Integration
def test_should_allow_get_user_by_id_for_self() -> None:
    """Valida que get user by id funciona cuando coincide con el usuario autenticado."""
    client = create_test_client()
    use_case = StubUseCase(result=make_user("user-1"))
    override_all_user_use_cases(client, use_case)
    client.app.dependency_overrides[get_authenticated_user] = lambda: make_user("user-1")

    response = client.get("/v1/users/user-1")

    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user-1"


# Tipo de test: Integration
def test_should_return_404_when_update_user_is_not_self() -> None:
    """Valida que update user responde 404 cuando se intenta actualizar otro usuario."""
    client = create_test_client()
    use_case = StubUseCase(result=make_user("other-user"))
    override_all_user_use_cases(client, use_case)
    client.app.dependency_overrides[get_authenticated_user] = lambda: make_user("user-1")

    response = client.put(
        "/v1/users/other-user",
        json={
            "name": "Ana",
            "lastname": "Lopez",
            "email": "ana@mail.com",
            "birthdate": "2000-01-01",
        },
    )

    assert response.status_code == 404
    assert response.json()["message"] == "user not found"
    assert use_case.received is None
