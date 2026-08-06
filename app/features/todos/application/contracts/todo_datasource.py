from abc import ABC, abstractmethod

from app.features.todos.domain.entities.todo import Todo


class TodoDatasource(ABC):
    """Application port for todo persistence operations."""

    @abstractmethod
    def create_todo(self, todo: Todo) -> Todo:
        """Persist a todo entity already validated by the domain."""
        pass

    @abstractmethod
    def get_todos_by_user_id(self, user_id: str, limit: int, offset: int) -> list[Todo]:
        pass

    @abstractmethod
    def count_todos_by_user_id(self, user_id: str) -> int:
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
