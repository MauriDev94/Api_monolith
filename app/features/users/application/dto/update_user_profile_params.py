from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class UpdateUserProfileParams:
    """Input DTO for updating non-email user profile fields."""

    id: str
    name: str
    lastname: str
    birthdate: date
