from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import NotFoundError
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.dto.create_todo_params import CreateTodoParams
from app.features.todos.application.dto.delete_todo_params import DeleteTodoParams
from app.features.todos.application.dto.get_todo_by_id_params import GetTodoByIdParams
from app.features.todos.application.dto.get_todos_params import GetTodosParams
from app.features.todos.application.dto.get_todos_result import GetTodosResult
from app.features.todos.application.dto.update_todo_params import UpdateTodoParams
from app.features.todos.application.usecases.create_todo_use_case import CreateTodo
from app.features.todos.application.usecases.delete_todo_use_case import DeleteTodo
from app.features.todos.application.usecases.get_todo_by_id_use_case import GetTodoById
from app.features.todos.application.usecases.get_todos_use_case import GetTodos
from app.features.todos.application.usecases.update_todo_use_case import UpdateTodo
from app.features.todos.domain.entities.todo import Todo


def make_todo(*, user_id: str = "user-1", is_completed: bool = False) -> Todo:
    return Todo(
        id="todo-1",
        user_id=user_id,
        title="Buy milk",
        description="at supermarket",
        is_completed=is_completed,
    )


# Tipo de test: Unit
def test_should_build_domain_entity_before_delegating_create_to_datasource() -> None:
    """Valida que create construye la entidad de dominio y le pasa esa entidad al datasource."""
    datasource = Mock(spec=TodoDatasource)
    expected_todo = make_todo()
    datasource.create_todo.return_value = expected_todo
    use_case = CreateTodo(todo_datasource=datasource)
    params = CreateTodoParams(user_id="user-1", title="  Buy milk  ", description="at supermarket")

    result = use_case.execute(params)

    datasource.create_todo.assert_called_once()
    entity = datasource.create_todo.call_args.args[0]
    assert isinstance(entity, Todo)
    assert entity.id is None
    assert entity.user_id == "user-1"
    assert entity.title == "Buy milk"
    assert entity.is_completed is False
    assert result == expected_todo


# Tipo de test: Unit
def test_should_reject_past_due_date_before_touching_the_datasource_on_create() -> None:
    """Valida que create falla en el dominio y NO llega a persistir cuando la fecha es pasada."""
    datasource = Mock(spec=TodoDatasource)
    use_case = CreateTodo(todo_datasource=datasource)
    params = CreateTodoParams(
        user_id="user-1",
        title="Buy milk",
        description=None,
        due_date=datetime.now(UTC) - timedelta(days=1),
    )

    with pytest.raises(ValueError, match="due_date cannot be in the past"):
        use_case.execute(params)

    datasource.create_todo.assert_not_called()


# Tipo de test: Unit
def test_should_reject_empty_title_before_touching_the_datasource_on_create() -> None:
    """Valida que un titulo vacio se rechaza en el dominio, sin escribir en la base."""
    datasource = Mock(spec=TodoDatasource)
    use_case = CreateTodo(todo_datasource=datasource)
    params = CreateTodoParams(user_id="user-1", title="   ", description=None)

    with pytest.raises(ValueError, match="title cannot be empty"):
        use_case.execute(params)

    datasource.create_todo.assert_not_called()


# Tipo de test: Unit
def test_should_delegate_get_todos_by_user_id_to_datasource_with_pagination() -> None:
    """Valida que get-todos delega al datasource por user_id con limit/offset y empaqueta el total."""
    datasource = Mock(spec=TodoDatasource)
    expected_todos = [make_todo()]
    datasource.get_todos_by_user_id.return_value = expected_todos
    datasource.count_todos_by_user_id.return_value = 1
    use_case = GetTodos(todo_datasource=datasource)

    result = use_case.execute(GetTodosParams(user_id="user-1", limit=20, offset=0))

    datasource.get_todos_by_user_id.assert_called_once_with("user-1", 20, 0)
    datasource.count_todos_by_user_id.assert_called_once_with("user-1")
    assert result == GetTodosResult(todos=expected_todos, total=1, limit=20, offset=0)


# Tipo de test: Unit
def test_should_raise_not_found_when_get_todo_by_id_returns_none() -> None:
    """Valida que get-by-id lanza not-found cuando no existe."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = None
    use_case = GetTodoById(todo_datasource=datasource)

    with pytest.raises(NotFoundError, match="todo not found"):
        use_case.execute(GetTodoByIdParams(todo_id="missing", user_id="user-1"))


# Tipo de test: Unit
def test_should_raise_not_found_when_get_todo_by_id_user_is_not_owner() -> None:
    """Valida que get-by-id lanza not-found cuando el usuario no es owner."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = make_todo(user_id="other-user")
    use_case = GetTodoById(todo_datasource=datasource)

    with pytest.raises(NotFoundError, match="todo not found"):
        use_case.execute(GetTodoByIdParams(todo_id="todo-1", user_id="user-1"))


# Tipo de test: Unit
def test_should_return_todo_when_get_todo_by_id_user_is_owner() -> None:
    """Valida que get-by-id retorna tarea cuando el usuario es owner."""
    datasource = Mock(spec=TodoDatasource)
    expected_todo = make_todo(user_id="user-1")
    datasource.get_todo_by_id.return_value = expected_todo
    use_case = GetTodoById(todo_datasource=datasource)

    result = use_case.execute(GetTodoByIdParams(todo_id="todo-1", user_id="user-1"))

    datasource.get_todo_by_id.assert_called_once_with("todo-1")
    assert result == expected_todo


# Tipo de test: Unit
def test_should_raise_not_found_when_update_target_does_not_exist() -> None:
    """Valida que update lanza not-found cuando la tarea no existe."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = None
    use_case = UpdateTodo(todo_datasource=datasource)
    params = UpdateTodoParams(
        todo_id="todo-1",
        user_id="user-1",
        title="New title",
        description="New desc",
        is_completed=True,
    )

    with pytest.raises(NotFoundError, match="todo not found"):
        use_case.execute(params)


# Tipo de test: Unit
def test_should_raise_not_found_when_update_target_belongs_to_other_user() -> None:
    """Valida que update lanza not-found cuando la tarea pertenece a otro usuario."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = make_todo(user_id="other-user")
    use_case = UpdateTodo(todo_datasource=datasource)
    params = UpdateTodoParams(
        todo_id="todo-1",
        user_id="user-1",
        title="New title",
        description="New desc",
        is_completed=True,
    )

    with pytest.raises(NotFoundError, match="todo not found"):
        use_case.execute(params)


# Tipo de test: Unit
def test_should_mutate_and_persist_todo_when_update_marks_completed() -> None:
    """Valida que update muta la entidad y persiste estado completado."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = make_todo(user_id="user-1", is_completed=False)
    expected = make_todo(user_id="user-1", is_completed=True)
    expected.title = "New title"
    expected.description = "New desc"
    datasource.update_todo.return_value = expected
    use_case = UpdateTodo(todo_datasource=datasource)

    result = use_case.execute(
        UpdateTodoParams(
            todo_id="todo-1",
            user_id="user-1",
            title="New title",
            description="New desc",
            is_completed=True,
        )
    )

    datasource.update_todo.assert_called_once()
    persisted_todo = datasource.update_todo.call_args.args[0]
    assert persisted_todo.title == "New title"
    assert persisted_todo.description == "New desc"
    assert persisted_todo.is_completed is True
    assert result == expected


# Tipo de test: Unit
def test_should_apply_due_date_when_update_provides_a_new_one() -> None:
    """Valida que update aplica el due_date recibido a la entidad persistida."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = make_todo(user_id="user-1")
    use_case = UpdateTodo(todo_datasource=datasource)
    new_due_date = datetime.now(UTC) + timedelta(days=5)

    use_case.execute(
        UpdateTodoParams(
            todo_id="todo-1",
            user_id="user-1",
            title="Buy milk",
            description=None,
            is_completed=False,
            due_date=new_due_date,
        )
    )

    persisted_todo = datasource.update_todo.call_args.args[0]
    assert persisted_todo.due_date == new_due_date


# Tipo de test: Unit
def test_should_clear_due_date_when_update_sends_none() -> None:
    """Valida que update con due_date None limpia la fecha (PUT = reemplazo total)."""
    datasource = Mock(spec=TodoDatasource)
    existing = make_todo(user_id="user-1")
    existing.due_date = datetime.now(UTC) + timedelta(days=5)
    datasource.get_todo_by_id.return_value = existing
    use_case = UpdateTodo(todo_datasource=datasource)

    use_case.execute(
        UpdateTodoParams(
            todo_id="todo-1",
            user_id="user-1",
            title="Buy milk",
            description=None,
            is_completed=False,
            due_date=None,
        )
    )

    persisted_todo = datasource.update_todo.call_args.args[0]
    assert persisted_todo.due_date is None


# Tipo de test: Unit
def test_should_allow_updating_an_overdue_todo_when_due_date_does_not_change() -> None:
    """Valida que editar una tarea vencida sin cambiar la fecha no dispara la regla de fecha pasada."""
    datasource = Mock(spec=TodoDatasource)
    past_due_date = datetime.now(UTC) - timedelta(days=2)
    existing = make_todo(user_id="user-1")
    existing.due_date = past_due_date
    datasource.get_todo_by_id.return_value = existing
    use_case = UpdateTodo(todo_datasource=datasource)

    use_case.execute(
        UpdateTodoParams(
            todo_id="todo-1",
            user_id="user-1",
            title="Titulo corregido",
            description=None,
            is_completed=False,
            due_date=past_due_date,
        )
    )

    persisted_todo = datasource.update_todo.call_args.args[0]
    assert persisted_todo.title == "Titulo corregido"
    assert persisted_todo.due_date == past_due_date


# Tipo de test: Unit
def test_should_mutate_and_persist_todo_when_update_marks_pending() -> None:
    """Valida que update muta la entidad y persiste estado pendiente."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = make_todo(user_id="user-1", is_completed=True)
    expected = make_todo(user_id="user-1", is_completed=False)
    expected.title = "Buy milk"
    expected.description = None
    datasource.update_todo.return_value = expected
    use_case = UpdateTodo(todo_datasource=datasource)

    result = use_case.execute(
        UpdateTodoParams(
            todo_id="todo-1",
            user_id="user-1",
            title="Buy milk",
            description=None,
            is_completed=False,
        )
    )

    datasource.update_todo.assert_called_once()
    persisted_todo = datasource.update_todo.call_args.args[0]
    assert persisted_todo.is_completed is False
    assert result == expected


# Tipo de test: Unit
def test_should_raise_not_found_when_delete_target_does_not_exist() -> None:
    """Valida que delete lanza not-found cuando la tarea no existe."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = None
    use_case = DeleteTodo(todo_datasource=datasource)

    with pytest.raises(NotFoundError, match="todo not found"):
        use_case.execute(DeleteTodoParams(todo_id="todo-1", user_id="user-1"))


# Tipo de test: Unit
def test_should_raise_not_found_when_delete_target_belongs_to_other_user() -> None:
    """Valida que delete lanza not-found cuando la tarea pertenece a otro usuario."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = make_todo(user_id="other-user")
    use_case = DeleteTodo(todo_datasource=datasource)

    with pytest.raises(NotFoundError, match="todo not found"):
        use_case.execute(DeleteTodoParams(todo_id="todo-1", user_id="user-1"))


# Tipo de test: Unit
def test_should_delegate_delete_when_todo_belongs_to_user() -> None:
    """Valida que delete delega al datasource cuando el usuario es owner."""
    datasource = Mock(spec=TodoDatasource)
    datasource.get_todo_by_id.return_value = make_todo(user_id="user-1")
    use_case = DeleteTodo(todo_datasource=datasource)

    use_case.execute(DeleteTodoParams(todo_id="todo-1", user_id="user-1"))

    datasource.delete_todo.assert_called_once_with("todo-1")
