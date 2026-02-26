from dataclasses import dataclass


@dataclass(slots=True)
class TokenPairResult:
    """Output DTO with access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
