from abc import ABC, abstractmethod
from datetime import datetime

from app.features.todos.application.dto.create_todo_params import CreateTodoParams
from app.features.todos.domain.entities.todo import Todo


class TodoDatasource(ABC):
    """Application port for todo persistence operations."""

    @abstractmethod
    def create_todo(self, params: CreateTodoParams) -> Todo:
        pass

    @abstractmethod
    def get_todos_by_user_id(self, user_id: str) -> list[Todo]:
        pass

    @abstractmethod
    def get_todo_by_id(self, todo_id: str) -> Todo | None:
        pass

    @abstractmethod
    def update_todo(self, todo: Todo) -> Todo:
        pass

    @abstractmethod
    def delete_todo(self, todo_id: str) -> None:
        pass

    @abstractmethod
    def get_todos_with_upcoming_due_date(
        self, days_ahead: int, current_time: datetime
    ) -> list[Todo]:
        """Return all incomplete todos with due_date within the specified days."""
        pass
