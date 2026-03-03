from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.providers.db import get_db_session
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.application.usecases.create_todo_use_case import CreateTodo
from app.features.todos.application.usecases.delete_todo_use_case import DeleteTodo
from app.features.todos.application.usecases.get_todo_by_id_use_case import GetTodoById
from app.features.todos.application.usecases.get_todos_use_case import GetTodos
from app.features.todos.application.usecases.update_todo_use_case import UpdateTodo
from app.features.todos.infrastructure.repositories.todo_repository import TodoRepository


def get_todo_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> TodoDatasource:
    """Provide SQLAlchemy-backed datasource for todo use cases."""
    return TodoRepository(session=db_session)


def get_create_todo_use_case(
    todo_datasource: Annotated[TodoDatasource, Depends(get_todo_repository)],
) -> CreateTodo:
    """Provide CreateTodo use case."""
    return CreateTodo(todo_datasource=todo_datasource)


def get_get_todos_use_case(
    todo_datasource: Annotated[TodoDatasource, Depends(get_todo_repository)],
) -> GetTodos:
    """Provide GetTodos use case."""
    return GetTodos(todo_datasource=todo_datasource)


def get_get_todo_by_id_use_case(
    todo_datasource: Annotated[TodoDatasource, Depends(get_todo_repository)],
) -> GetTodoById:
    """Provide GetTodoById use case."""
    return GetTodoById(todo_datasource=todo_datasource)


def get_update_todo_use_case(
    todo_datasource: Annotated[TodoDatasource, Depends(get_todo_repository)],
) -> UpdateTodo:
    """Provide UpdateTodo use case."""
    return UpdateTodo(todo_datasource=todo_datasource)


def get_delete_todo_use_case(
    todo_datasource: Annotated[TodoDatasource, Depends(get_todo_repository)],
) -> DeleteTodo:
    """Provide DeleteTodo use case."""
    return DeleteTodo(todo_datasource=todo_datasource)
