from datetime import date

from sqlalchemy.orm import Session

from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.todos.application.dto.create_todo_params import CreateTodoParams
from app.features.todos.application.dto.update_todo_params import UpdateTodoParams
from app.features.todos.infrastructure.repositories.todo_repository import TodoRepository


def _seed_user(session: Session, email: str = "mauri@mail.com") -> str:
    # Creates a valid persisted owner user used by todo foreign key.
    auth_repository = AuthRepository(session=session)
    user = auth_repository.register_user(
        params=RegisterUserParams(
            name="Mauri",
            lastname="Salinas",
            email=email,
            password="plain1234",
            birthdate=date(2000, 1, 1),
        ),
        password_hash="hashed-password",
    )
    return user.id or ""


# Validates create flow writes a todo row and maps it back to entity.
# Tipo de test: Integration
def test_should_create_todo_for_existing_user(db_session: Session) -> None:
    """Valida que crear tarea para existente usuario."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)

    todo = repository.create_todo(
        CreateTodoParams(
            user_id=user_id,
            title="Study",
            description="Study programming concepts",
        )
    )

    assert todo.id is not None
    assert todo.user_id == user_id
    assert todo.title == "Study"
    assert todo.is_completed is False


# Ensures list query filters and returns all todos for the owner.
# Tipo de test: Integration
def test_should_return_todos_by_user_id(db_session: Session) -> None:
    """Valida que retorna tareas por usuario id."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)

    repository.create_todo(CreateTodoParams(user_id=user_id, title="Task 1", description=None))
    repository.create_todo(CreateTodoParams(user_id=user_id, title="Task 2", description="desc"))

    todos = repository.get_todos_by_user_id(user_id)

    assert len(todos) == 2
    titles = {todo.title for todo in todos}
    assert titles == {"Task 1", "Task 2"}


# Checks direct retrieval by id from persistence layer.
# Tipo de test: Integration
def test_should_get_todo_by_id(db_session: Session) -> None:
    """Valida que obtener tarea por id."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(CreateTodoParams(user_id=user_id, title="Study", description=None))

    todo = repository.get_todo_by_id(created.id or "")

    assert todo is not None
    assert todo.id == created.id
    assert todo.user_id == user_id


# Verifies updated fields are committed and returned correctly.
# Tipo de test: Integration
def test_should_update_todo(db_session: Session) -> None:
    """Valida que actualizar tarea."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(CreateTodoParams(user_id=user_id, title="Study", description=None))

    updated = repository.update_todo(
        UpdateTodoParams(
            todo_id=created.id or "",
            user_id=user_id,
            title="Study DDD",
            description="Clean architecture",
            is_completed=True,
        )
    )

    assert updated.id == created.id
    assert updated.title == "Study DDD"
    assert updated.description == "Clean architecture"
    assert updated.is_completed is True


# Confirms deletion removes row and repository returns None contract.
# Tipo de test: Integration
def test_should_delete_todo(db_session: Session) -> None:
    """Valida que eliminar tarea."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(CreateTodoParams(user_id=user_id, title="Study", description=None))

    result = repository.delete_todo(created.id or "")

    assert result is None
    assert repository.get_todo_by_id(created.id or "") is None


# Documents idempotent behavior for missing todo on get/delete.
# Tipo de test: Integration
def test_should_return_none_when_getting_or_deleting_missing_todo(db_session: Session) -> None:
    """Valida que retorna ninguno cuando getting o deleting faltante tarea."""
    repository = TodoRepository(session=db_session)

    missing_todo = repository.get_todo_by_id("missing-id")
    result = repository.delete_todo("missing-id")

    assert missing_todo is None
    assert result is None
