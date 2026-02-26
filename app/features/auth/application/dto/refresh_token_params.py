from dataclasses import dataclass


@dataclass(slots=True)
class RefreshTokenParams:
    """Input DTO for refresh token flow."""

    refresh_token: str
