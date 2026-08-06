from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.features.todos.domain.entities.todo import Todo
from app.features.todos.infrastructure.repositories.todo_repository import TodoRepository
from app.features.users.domain.entities.user import User
from app.features.users.infrastructure.repositories.user_provider_repository import (
    UserProviderRepository,
)


def _seed_user(session: Session, email: str = "mauri@mail.com") -> str:
    provider = UserProviderRepository(session=session)
    user = provider.create_user(
        User.create_new(
            name="Mauri",
            lastname="Salinas",
            email=email,
            password_hash="hashed-password",
            birthdate=date(2000, 1, 1),
        )
    )
    return user.id or ""


def _new_todo(
    user_id: str,
    title: str,
    description: str | None = None,
    due_date: datetime | None = None,
) -> Todo:
    """Construye la entidad como lo hace el use case: a través del factory de dominio."""
    return Todo.create_new(user_id=user_id, title=title, description=description, due_date=due_date)


# Tipo de test: Integration
def test_should_create_todo_for_existing_user(db_session: Session) -> None:
    """Valida que create persiste una tarea para un usuario existente."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)

    todo = repository.create_todo(
        _new_todo(user_id, "Study", description="Study programming concepts")
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

    repository.create_todo(_new_todo(user_id, "Task 1"))
    repository.create_todo(_new_todo(user_id, "Task 2", description="desc"))

    todos = repository.get_todos_by_user_id(user_id, limit=20, offset=0)

    assert len(todos) == 2
    titles = {todo.title for todo in todos}
    assert titles == {"Task 1", "Task 2"}


# Tipo de test: Integration
def test_should_return_first_page_when_limit_is_smaller_than_total(db_session: Session) -> None:
    """Valida que la página 1 retorna solo `limit` elementos en orden estable."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    for index in range(3):
        repository.create_todo(_new_todo(user_id, f"Task {index}"))

    page_one = repository.get_todos_by_user_id(user_id, limit=2, offset=0)

    assert len(page_one) == 2
    assert [todo.title for todo in page_one] == ["Task 0", "Task 1"]


# Tipo de test: Integration
def test_should_return_second_page_when_offset_is_applied(db_session: Session) -> None:
    """Valida que el offset desplaza correctamente la ventana de paginación."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    for index in range(3):
        repository.create_todo(_new_todo(user_id, f"Task {index}"))

    page_two = repository.get_todos_by_user_id(user_id, limit=2, offset=2)

    assert len(page_two) == 1
    assert page_two[0].title == "Task 2"


# Tipo de test: Integration
def test_should_count_todos_by_user_id(db_session: Session) -> None:
    """Valida que count-todos retorna el total de tareas del owner, ignorando otros usuarios."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    other_user_id = _seed_user(db_session, email="otra@mail.com")
    repository.create_todo(_new_todo(user_id, "Task 1"))
    repository.create_todo(_new_todo(user_id, "Task 2"))
    repository.create_todo(_new_todo(other_user_id, "Other task"))

    total = repository.count_todos_by_user_id(user_id)

    assert total == 2


# Tipo de test: Integration
def test_should_get_todo_by_id(db_session: Session) -> None:
    """Valida que get-by-id retorna la tarea persistida."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(_new_todo(user_id, "Study"))

    todo = repository.get_todo_by_id(created.id or "")

    assert todo is not None
    assert todo.id == created.id
    assert todo.user_id == user_id


# Tipo de test: Integration
def test_should_update_todo(db_session: Session) -> None:
    """Valida que update persiste estado mutado de la entidad tarea."""
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    created = repository.create_todo(_new_todo(user_id, "Study"))
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
    created = repository.create_todo(_new_todo(user_id, "Study"))

    repository.delete_todo(created.id or "")

    assert repository.get_todo_by_id(created.id or "") is None


# Tipo de test: Integration
def test_should_return_none_when_getting_or_deleting_missing_todo(db_session: Session) -> None:
    """Valida que get/delete de tarea inexistente mantiene contrato idempotente."""
    repository = TodoRepository(session=db_session)

    missing_todo = repository.get_todo_by_id("missing-id")
    repository.delete_todo("missing-id")

    assert missing_todo is None


# Tipo de test: Integration
def test_should_persist_and_read_todo_with_past_due_date(db_session: Session) -> None:
    """Reproduce O1+A2: un todo con due_date vencido debe poder persistirse y leerse
    sin romper. Antes, la rehidratación lanzaba ValueError → 500 en GET /todos.

    La entidad se construye por constructor directo, no por `create_new`: el factory
    rechaza fechas pasadas (regla de creación), pero una tarea vencida sí puede existir.
    """
    repository = TodoRepository(session=db_session)
    user_id = _seed_user(db_session)
    past_due = datetime.now(UTC) - timedelta(days=1)
    overdue_todo = Todo(
        id=None,
        user_id=user_id,
        title="Overdue",
        description=None,
        is_completed=False,
        due_date=past_due,
    )

    created = repository.create_todo(overdue_todo)

    fetched = repository.get_todo_by_id(created.id or "")

    assert fetched is not None
    assert fetched.due_date is not None
