from dataclasses import dataclass
from uuid import uuid4

from app.common.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class RefreshTokenId:
    """Value object representing the refresh token unique identifier (JTI)."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise DomainError("refresh token id cannot be empty")

    @classmethod
    def generate(cls) -> "RefreshTokenId":
        return cls(value=str(uuid4()))

    def __str__(self) -> str:
        return self.value
