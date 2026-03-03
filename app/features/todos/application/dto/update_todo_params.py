from dataclasses import dataclass


@dataclass(slots=True)
class UpdateTodoParams:
    """Input DTO for updating a todo item."""

    todo_id: str
    user_id: str
    title: str
    description: str | None
    is_completed: bool
