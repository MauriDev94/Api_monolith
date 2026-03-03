from dataclasses import dataclass


@dataclass(slots=True)
class CreateTodoParams:
    """Input DTO for creating a todo item."""

    user_id: str
    title: str
    description: str | None = None
