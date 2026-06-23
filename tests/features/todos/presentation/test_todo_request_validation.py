from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.features.todos.presentation.schemas.todo_requests import CreateTodoRequest


# Tipo de test: Integration
def test_should_reject_past_due_date_on_create_request() -> None:
    """A2: la regla 'no en el pasado' vive en el borde de entrada (422), no en el dominio."""
    past = datetime.now(UTC) - timedelta(days=1)

    with pytest.raises(ValidationError, match="due_date cannot be in the past"):
        CreateTodoRequest(title="Buy milk", due_date=past)


# Tipo de test: Integration
def test_should_accept_future_due_date_on_create_request() -> None:
    future = datetime.now(UTC) + timedelta(days=1)

    request = CreateTodoRequest(title="Buy milk", due_date=future)

    assert request.due_date == future


# Tipo de test: Integration
def test_should_accept_none_due_date_on_create_request() -> None:
    request = CreateTodoRequest(title="Buy milk")

    assert request.due_date is None
