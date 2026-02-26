from dataclasses import dataclass


@dataclass(slots=True)
class LoginUserParams:
    """Input DTO for login flow."""

    email: str
    password: str
