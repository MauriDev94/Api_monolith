from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class UpdateUserParams:
    """Input DTO for updating an existing user."""

    id: str
    name: str
    lastname: str
    email: str
    birthdate: date
