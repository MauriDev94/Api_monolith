from datetime import UTC, datetime, timedelta

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
    fields: dict[str, str] = {"user_id": "user-1", "title": "Buy milk"}
    fields[field] = value

    with pytest.raises(ValueError, match=f"{field} cannot be empty"):
        Todo(
            id="todo-1",
            user_id=fields["user_id"],
            title=fields["title"],
            description=None,
            is_completed=False,
        )


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


# Tipo de test: Unit
def test_should_accept_due_date_in_future() -> None:
    """Valida que acepta due_date en el futuro."""
    future_date = datetime.now(UTC) + timedelta(days=7)

    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=future_date,
    )

    assert todo.due_date is not None
    assert todo.due_date > datetime.now(UTC)


# Tipo de test: Unit
def test_should_accept_due_date_as_none() -> None:
    """Valida que acepta due_date como None."""
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=None,
    )

    assert todo.due_date is None


# Tipo de test: Unit
def test_should_accept_past_due_date_on_reconstruction() -> None:
    """Rehidratar un todo ya vencido (con id) NO debe lanzar: la regla 'no en el
    pasado' es de creación, no un invariante permanente. Antes esto rompía GET /todos."""
    past_date = datetime.now(UTC) - timedelta(days=1)

    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=past_date,
    )

    assert todo.due_date is not None
    assert todo.due_date.tzinfo is not None


# Tipo de test: Unit
def test_should_convert_naive_due_date_to_aware() -> None:
    """Valida que convierte due_date naive a timezone-aware."""
    naive_date = datetime(2026, 12, 31, 23, 59, 59)

    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=naive_date,
    )

    assert todo.due_date is not None
    assert todo.due_date.tzinfo is not None


# Tipo de test: Unit
def test_should_set_due_date_with_validation() -> None:
    """Valida que set_due_date valida correctamente."""
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
    )

    future_date = datetime.now(UTC) + timedelta(days=7)
    todo.set_due_date(future_date)

    assert todo.due_date == future_date


# Tipo de test: Unit
def test_should_raise_when_setting_past_due_date() -> None:
    """set_due_date rechaza fechas en el pasado (mutación explícita del usuario)."""
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
    )

    past_date = datetime.now(UTC) - timedelta(days=1)
    with pytest.raises(ValueError, match="due_date cannot be in the past"):
        todo.set_due_date(past_date)


# Tipo de test: Unit
def test_should_not_revalidate_due_date_when_value_does_not_change() -> None:
    """set_due_date es no-op si el valor no cambia: la regla 'no en el pasado' aplica a fechas NUEVAS.

    Sin esto, editar el titulo de una tarea ya vencida reenviando su misma fecha
    fallaria con DomainError.
    """
    past_date = datetime.now(UTC) - timedelta(days=3)
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=past_date,
    )

    todo.set_due_date(past_date)

    assert todo.due_date == past_date
    assert todo.updated_at is None


# Tipo de test: Unit
def test_should_treat_naive_due_date_as_unchanged_when_equal_to_current() -> None:
    """set_due_date normaliza antes de comparar: una fecha naive igual a la actual no cambia nada."""
    past_date = datetime.now(UTC) - timedelta(days=3)
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=past_date,
    )

    todo.set_due_date(past_date.replace(tzinfo=None))

    assert todo.due_date == past_date
    assert todo.updated_at is None


# Tipo de test: Unit
def test_should_clear_due_date_when_setting_none() -> None:
    """set_due_date(None) limpia la fecha: semantica de reemplazo total en PUT."""
    future_date = datetime.now(UTC) + timedelta(days=7)
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=future_date,
    )

    todo.set_due_date(None)

    assert todo.due_date is None
    assert todo.updated_at is not None


# Tipo de test: Unit
def test_should_remove_due_date() -> None:
    """Valida que remove_due_date funciona."""
    future_date = datetime.now(UTC) + timedelta(days=7)
    todo = Todo(
        id="todo-1",
        user_id="user-1",
        title="Buy milk",
        description=None,
        is_completed=False,
        due_date=future_date,
    )

    todo.remove_due_date()

    assert todo.due_date is None
