from dataclasses import dataclass


@dataclass(slots=True)
class ChangeUserEmailParams:
    """Input DTO for changing user email."""

    id: str
    email: str
