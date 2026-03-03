from dataclasses import FrozenInstanceError

import pytest

from app.features.todos.domain.entities.todo import Todo


def test_should_normalize_todo_text_fields() -> None:
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


def test_should_convert_blank_description_to_none() -> None:
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description="   ",
        is_completed=False,
    )

    assert todo.description is None


@pytest.mark.parametrize("field,value", [("user_id", "   "), ("title", "")])
def test_should_raise_when_required_text_field_is_empty(field: str, value: str) -> None:
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


def test_should_be_immutable() -> None:
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
    )

    with pytest.raises(FrozenInstanceError):
        todo.title = "New title"
