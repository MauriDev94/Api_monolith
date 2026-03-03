from dataclasses import dataclass


@dataclass(slots=True)
class DeleteTodoParams:
    """Input DTO for deleting a todo item."""

    todo_id: str
    user_id: str
