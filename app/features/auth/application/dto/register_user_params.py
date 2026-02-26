from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class RegisterUserParams:
    """Input DTO for user registration flow."""

    name: str
    lastname: str
    email: str
    password: str
    birthdate: date
