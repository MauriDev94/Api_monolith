from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UpdateTodoParams:
    """Input DTO for updating a todo item."""

    todo_id: str
    user_id: str
    title: str
    description: str | None
    is_completed: bool
    due_date: datetime | None = None
