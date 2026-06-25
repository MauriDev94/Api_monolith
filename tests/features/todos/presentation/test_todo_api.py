from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions.error_handling import register_exception_handlers
from app.core.exceptions.exceptions import NotFoundError
from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.todos.application.dto.get_todos_result import GetTodosResult
from app.features.todos.di.dependencies import (
    get_create_todo_use_case,
    get_delete_todo_use_case,
    get_get_todo_by_id_use_case,
    get_get_todos_use_case,
    get_update_todo_use_case,
)
from app.features.todos.domain.entities.todo import Todo
from app.features.todos.presentation.api import v1_router
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class StubUseCase:
    def __init__(self, result=None, exc: Exception | None = None):
        self.result = result
        self.exc = exc
        self.received: Any = None

    def execute(self, params=None):
        self.received = params
        if self.exc is not None:
            raise self.exc
        return self.result


def make_user() -> User:
    return User(
        id="user-1",
        name="Mauri",
        lastname="Salinas",
        email=Email("mauri@mail.com"),
        password_hash="hashed-password",
        birthdate=date(2000, 1, 1),
    )


def make_todo() -> Todo:
    return Todo(
        id="todo-1",
        user_id="user-1",
        title="Study",
        description="Study programming concepts",
        is_completed=False,
    )


def create_test_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(v1_router)
    return TestClient(app, raise_server_exceptions=False)


def override_all_todo_use_cases(client: TestClient, use_case: StubUseCase) -> None:
    app = client.app
    app.dependency_overrides[get_create_todo_use_case] = lambda: use_case
    app.dependency_overrides[get_get_todos_use_case] = lambda: use_case
    app.dependency_overrides[get_get_todo_by_id_use_case] = lambda: use_case
    app.dependency_overrides[get_update_todo_use_case] = lambda: use_case
    app.dependency_overrides[get_delete_todo_use_case] = lambda: use_case


# Tipo de test: Integration
def test_should_return_401_when_missing_bearer_token() -> None:
    """Valida que retorna 401 cuando faltante bearer token."""
    client = create_test_client()
    override_all_todo_use_cases(client, StubUseCase(result=[]))

    response = client.get("/v1/todos")

    assert response.status_code == 401
    assert response.json()["message"] == "Not authenticated"


# Tipo de test: Integration
def test_should_create_todo_when_authenticated() -> None:
    """Valida que crear tarea cuando autenticado."""
    client = create_test_client()
    create_use_case = StubUseCase(result=make_todo())
    override_all_todo_use_cases(client, StubUseCase(result=None))
    client.app.dependency_overrides[get_create_todo_use_case] = lambda: create_use_case
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/v1/todos",
        json={"title": "  Study  ", "description": "Study programming concepts"},
    )

    assert response.status_code == 201
    assert response.json()["todo"]["id"] == "todo-1"
    assert create_use_case.received.user_id == "user-1"
    assert create_use_case.received.title == "Study"


# Tipo de test: Integration
def test_should_list_todos_for_authenticated_user_with_default_pagination() -> None:
    """Valida que listar tareas usa limit=20/offset=0 por defecto y retorna metadata."""
    client = create_test_client()
    list_use_case = StubUseCase(
        result=GetTodosResult(todos=[make_todo()], total=1, limit=20, offset=0)
    )
    override_all_todo_use_cases(client, StubUseCase(result=None))
    client.app.dependency_overrides[get_get_todos_use_case] = lambda: list_use_case
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.get("/v1/todos")

    assert response.status_code == 200
    body = response.json()
    assert len(body["todos"]) == 1
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert list_use_case.received.user_id == "user-1"
    assert list_use_case.received.limit == 20
    assert list_use_case.received.offset == 0


# Tipo de test: Integration
def test_should_list_todos_with_custom_limit_and_offset() -> None:
    """Valida que limit/offset pasados por query se propagan al caso de uso."""
    client = create_test_client()
    list_use_case = StubUseCase(
        result=GetTodosResult(todos=[make_todo()], total=5, limit=2, offset=2)
    )
    override_all_todo_use_cases(client, StubUseCase(result=None))
    client.app.dependency_overrides[get_get_todos_use_case] = lambda: list_use_case
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.get("/v1/todos?limit=2&offset=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 2
    assert list_use_case.received.limit == 2
    assert list_use_case.received.offset == 2


# Tipo de test: Integration
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_should_return_400_when_pagination_params_are_out_of_range(query: str) -> None:
    """Valida que limit/offset fuera de rango retornan 400 (validación de transporte).

    FastAPI emite 422 para violaciones de `Query(...)`, pero el handler global de
    `RequestValidationError` del repo las normaliza a 400 (ver error_handling.py)."""
    client = create_test_client()
    override_all_todo_use_cases(client, StubUseCase(result=None))
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.get(f"/v1/todos?{query}")

    assert response.status_code == 400


# Tipo de test: Integration
def test_should_return_404_when_get_todo_by_id_use_case_raises_not_found() -> None:
    """Valida que retorna 404 cuando obtener una tarea por id caso de uso lanza un error de no encontrado."""
    client = create_test_client()
    get_by_id_use_case = StubUseCase(exc=NotFoundError("todo not found"))
    override_all_todo_use_cases(client, StubUseCase(result=None))
    client.app.dependency_overrides[get_get_todo_by_id_use_case] = lambda: get_by_id_use_case
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.get("/v1/todos/missing-id")

    assert response.status_code == 404
    assert response.json()["message"] == "todo not found"
