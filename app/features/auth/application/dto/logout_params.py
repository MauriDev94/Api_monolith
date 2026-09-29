from dataclasses import dataclass


@dataclass(slots=True)
class LogoutParams:
    """Input DTO for the logout flow."""

    user_id: str
