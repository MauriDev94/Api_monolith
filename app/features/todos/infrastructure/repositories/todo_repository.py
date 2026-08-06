from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import DatabaseError, NotFoundError
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.todos.domain.entities.todo import Todo
from app.features.todos.infrastructure.mappers.todo_mapper import (
    map_new_todo_entity_to_model,
    map_todo_entity_to_model,
    map_todo_model_to_entity,
)
from app.features.todos.infrastructure.models.todo_model import TodoModel


class TodoRepository(TodoDatasource):
    """SQLAlchemy implementation for todo persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    def create_todo(self, todo: Todo) -> Todo:
        todo_model = map_new_todo_entity_to_model(todo, todo_id=str(uuid4()))

        try:
            self.session.add(todo_model)
            self.session.commit()
            self.session.refresh(todo_model)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to create todo") from exc

        return map_todo_model_to_entity(todo_model)

    def get_todos_by_user_id(self, user_id: str, limit: int, offset: int) -> list[Todo]:
        try:
            todos_model = (
                self.session.query(TodoModel)
                .filter(TodoModel.user_id == user_id)
                .order_by(TodoModel.created_at, TodoModel.id)
                .limit(limit)
                .offset(offset)
                .all()
            )
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve todos") from exc

        return [map_todo_model_to_entity(todo_model) for todo_model in todos_model]

    def count_todos_by_user_id(self, user_id: str) -> int:
        try:
            return self.session.query(TodoModel).filter(TodoModel.user_id == user_id).count()
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to count todos") from exc

    def get_todo_by_id(self, todo_id: str) -> Todo | None:
        try:
            todo_model = self.session.query(TodoModel).filter(TodoModel.id == todo_id).first()
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve todo by id") from exc

        if todo_model is None:
            return None
        return map_todo_model_to_entity(todo_model)

    def update_todo(self, todo: Todo) -> Todo:
        if todo.id is None:
            raise NotFoundError("todo not found")

        try:
            todo_model = self.session.query(TodoModel).filter(TodoModel.id == todo.id).first()
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve todo for update") from exc

        if todo_model is None:
            raise NotFoundError("todo not found")

        map_todo_entity_to_model(todo_model=todo_model, todo=todo)

        try:
            self.session.commit()
            self.session.refresh(todo_model)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to update todo") from exc

        return map_todo_model_to_entity(todo_model)

    def delete_todo(self, todo_id: str) -> None:
        try:
            todo_model = self.session.query(TodoModel).filter(TodoModel.id == todo_id).first()
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve todo for deletion") from exc

        if todo_model is None:
            return None

        try:
            self.session.delete(todo_model)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to delete todo") from exc

        return None
