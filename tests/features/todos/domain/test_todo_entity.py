from dataclasses import FrozenInstanceError

import pytest

from app.features.todos.domain.entities.todo import Todo


# Tipo de test: Unit
def test_should_normalize_todo_text_fields() -> None:
    """Valida que normaliza los campos de texto de la tarea."""
    todo = Todo(
        id="todo-1",
        user_id="  user-1  ",
        title="  Buy milk  ",
        description="  at supermarket  ",
        is_completed=False,
    )

    assert todo.user_id == "user-1"
    assert todo.title == "Buy milk"
    assert todo.description == "at supermarket"


# Tipo de test: Unit
def test_should_convert_blank_description_to_none() -> None:
    """Valida que convierte una descripcion vacia en None."""
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description="   ",
        is_completed=False,
    )

    assert todo.description is None


@pytest.mark.parametrize("field,value", [("user_id", "   "), ("title", "")])
# Tipo de test: Unit
def test_should_raise_when_required_text_field_is_empty(field: str, value: str) -> None:
    """Valida que lanza un error cuando un campo de texto requerido esta vacio."""
    kwargs = {
        "id": "todo-1",
        "user_id": "user-1",
        "title": "Buy milk",
        "description": None,
        "is_completed": False,
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=f"{field} cannot be empty"):
        Todo(**kwargs)


# Tipo de test: Unit
def test_should_be_immutable() -> None:
    """Valida que es inmutable."""
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
    )

    with pytest.raises(FrozenInstanceError):
        todo.title = "New title"
