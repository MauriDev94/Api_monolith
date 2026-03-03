from dataclasses import dataclass


@dataclass(slots=True)
class GetTodosParams:
    """Input DTO for listing todos by authenticated user."""

    user_id: str
