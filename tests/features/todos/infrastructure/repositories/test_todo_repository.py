from datetime import date

from sqlalchemy.orm import Session

from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.todos.application.dto.create_todo_params import CreateTodoParams
from app.features.todos.infrastructure.repositories.todo_repository import TodoRepository


def _seed_user(session: Session, email: str = "mauri@mail.com") -> str:
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


# Tipo de test: Integration
def test_should_create_todo_for_existing_user(db_session: Session) -> None:
    """Valida que create persiste una tarea para un usuario existente."""
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


# Tipo de test: Integration
def test_should_return_todos_by_user_id(db_session: Session) -> None:
    """Valida que get-todos filtra correctamente por owner."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)

    repository.create_todo(CreateTodoParams(user_id=user_id, title="Task 1", description=None))
    repository.create_todo(CreateTodoParams(user_id=user_id, title="Task 2", description="desc"))

    todos = repository.get_todos_by_user_id(user_id)

    assert len(todos) == 2
    titles = {todo.title for todo in todos}
    assert titles == {"Task 1", "Task 2"}


# Tipo de test: Integration
def test_should_get_todo_by_id(db_session: Session) -> None:
    """Valida que get-by-id retorna la tarea persistida."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(CreateTodoParams(user_id=user_id, title="Study", description=None))

    todo = repository.get_todo_by_id(created.id or "")

    assert todo is not None
    assert todo.id == created.id
    assert todo.user_id == user_id


# Tipo de test: Integration
def test_should_update_todo(db_session: Session) -> None:
    """Valida que update persiste estado mutado de la entidad tarea."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(CreateTodoParams(user_id=user_id, title="Study", description=None))
    todo = repository.get_todo_by_id(created.id or "")
    assert todo is not None

    todo.rename("Study DDD")
    todo.change_description("Clean architecture")
    todo.mark_completed()

    updated = repository.update_todo(todo)

    assert updated.id == created.id
    assert updated.title == "Study DDD"
    assert updated.description == "Clean architecture"
    assert updated.is_completed is True


# Tipo de test: Integration
def test_should_delete_todo(db_session: Session) -> None:
    """Valida que delete elimina la tarea."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(CreateTodoParams(user_id=user_id, title="Study", description=None))

    result = repository.delete_todo(created.id or "")

    assert result is None
    assert repository.get_todo_by_id(created.id or "") is None


# Tipo de test: Integration
def test_should_return_none_when_getting_or_deleting_missing_todo(db_session: Session) -> None:
    """Valida que get/delete de tarea inexistente mantiene contrato idempotente."""
    repository = TodoRepository(session=db_session)

    missing_todo = repository.get_todo_by_id("missing-id")
    result = repository.delete_todo("missing-id")

    assert missing_todo is None
    assert result is None
