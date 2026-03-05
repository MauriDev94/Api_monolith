import pytest

from app.features.todos.domain.entities.todo import Todo


# Tipo de test: Unit
def test_should_normalize_todo_text_fields() -> None:
    """Valida que normaliza los campos de texto al crear una tarea."""
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
    """Valida que una descripcion vacia se normaliza a None."""
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
    """Valida que lanza error cuando un campo de texto requerido esta vacio."""
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
def test_should_mutate_todo_with_behavior_methods() -> None:
    """Valida que los metodos de dominio mutan titulo, descripcion y estado."""
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
    )

    todo.rename(" Study DDD ")
    todo.change_description("  Read docs ")
    todo.mark_completed()

    assert todo.title == "Study DDD"
    assert todo.description == "Read docs"
    assert todo.is_completed is True
    assert todo.updated_at is not None

    todo.mark_pending()
    assert todo.is_completed is False


# Tipo de test: Unit
def test_should_raise_when_renaming_todo_with_invalid_title() -> None:
    """Valida que renombrar una tarea con titulo vacio lanza error."""
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
    )

    with pytest.raises(ValueError, match="title cannot be empty"):
        todo.rename("   ")
