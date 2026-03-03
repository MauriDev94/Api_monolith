from dataclasses import dataclass


@dataclass(slots=True)
class GetTodoByIdParams:
    """Input DTO for retrieving one todo by id for a specific user."""

    todo_id: str
    user_id: str
