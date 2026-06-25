from dataclasses import dataclass

from app.features.todos.domain.entities.todo import Todo


@dataclass(slots=True)
class GetTodosResult:
    """Output DTO for a paginated page of todos."""

    todos: list[Todo]
    total: int
    limit: int
    offset: int
