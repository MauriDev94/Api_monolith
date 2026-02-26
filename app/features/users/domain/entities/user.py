from dataclasses import dataclass
from datetime import date, datetime

from app.features.users.domain.value_objects.email import Email


@dataclass(frozen=True, slots=True)
class User:
    """Immutable domain user with basic normalization and invariants."""

    id: str | None
    name: str
    lastname: str
    email: Email
    password_hash: str
    birthdate: date
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Normalizes inputs and validates required business rules after creation.
    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self._require_text(self.name, "name"))
        object.__setattr__(self, "lastname", self._require_text(self.lastname, "lastname"))
        object.__setattr__(self, "email", self._normalize_email(self.email))
        object.__setattr__(
            self,
            "password_hash",
            self._require_text(self.password_hash, "password_hash"),
        )

        self._validate_birthdate(self.birthdate)

    @staticmethod
    # Ensures required text fields are not blank and returns trimmed text.
    def _require_text(value: str, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} cannot be empty")
        return normalized

    @staticmethod
    # Applies canonical formatting and validates a minimal email structure.
    def _normalize_email(email: str | Email) -> Email:
        if isinstance(email, Email):
            return email
        return Email(email)

    @staticmethod
    # Prevents dates of birth that are later than the current date.
    def _validate_birthdate(birthdate: date) -> None:
        if birthdate > date.today():
            raise ValueError("birthdate cannot be in the future")
