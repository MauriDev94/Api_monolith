from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.features.todos.presentation.schemas.todo_requests import CreateTodoRequest


# Tipo de test: Integration
def test_should_not_enforce_business_rules_in_the_request_schema() -> None:
    """El schema NO rechaza fechas pasadas: esa regla vive en `Todo.create_new()`.

    Si viviera acá, solo aplicaría a las peticiones HTTP y cualquier otra entrada
    (un seeder, un job, otro use case) crearía tareas saltándose la regla.
    """
    past = datetime.now(UTC) - timedelta(days=1)

    request = CreateTodoRequest(title="Buy milk", due_date=past)

    assert request.due_date == past


# Tipo de test: Integration
def test_should_accept_future_due_date_on_create_request() -> None:
    future = datetime.now(UTC) + timedelta(days=1)

    request = CreateTodoRequest(title="Buy milk", due_date=future)

    assert request.due_date == future


# Tipo de test: Integration
def test_should_accept_none_due_date_on_create_request() -> None:
    request = CreateTodoRequest(title="Buy milk")

    assert request.due_date is None


# Tipo de test: Integration
def test_should_still_enforce_transport_constraints_on_create_request() -> None:
    """Lo que sí es del transporte se queda: tamaño del payload."""
    with pytest.raises(ValidationError):
        CreateTodoRequest(title="x" * 151)
