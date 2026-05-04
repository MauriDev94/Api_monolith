from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.features.users.domain.value_objects.email import Email


@dataclass(slots=True)
class User:
    """Mutable domain user with normalization, invariants and behavior methods."""

    id: str | None
    name: str
    lastname: str
    email: Email
    password_hash: str | None
    birthdate: date
    google_id: str | None = None
    google_email_verified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self._require_text(self.name, "name")
        self.lastname = self._require_text(self.lastname, "lastname")
        self.email = self._normalize_email(self.email)
        self._validate_password_hash()
        self._validate_birthdate(self.birthdate)

    def change_name(self, new_name: str) -> None:
        """Change user name applying domain validation."""
        self.name = self._require_text(new_name, "name")
        self._mark_as_updated()

    def change_lastname(self, new_lastname: str) -> None:
        """Change user lastname applying domain validation."""
        self.lastname = self._require_text(new_lastname, "lastname")
        self._mark_as_updated()

    def change_email(self, new_email: Email | str) -> None:
        """Change user email applying value-object normalization."""
        self.email = self._normalize_email(new_email)
        self._mark_as_updated()

    def change_birthdate(self, new_birthdate: date) -> None:
        """Change user birthdate enforcing domain rules."""
        self._validate_birthdate(new_birthdate)
        self.birthdate = new_birthdate
        self._mark_as_updated()

    def change_password_hash(self, new_hash: str) -> None:
        """Set or change the password hash for this user."""
        if not new_hash or not new_hash.strip():
            raise ValueError("password_hash cannot be empty")
        self.password_hash = new_hash
        self._mark_as_updated()

    def _validate_password_hash(self) -> None:
        """Validate password_hash only when it's present (not None)."""
        if self.password_hash is not None:
            self.password_hash = self.password_hash.strip()
            if not self.password_hash:
                raise ValueError("password_hash cannot be empty")

    def _mark_as_updated(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} cannot be empty")
        return normalized

    @staticmethod
    def _normalize_email(email: str | Email) -> Email:
        if isinstance(email, Email):
            return email
        return Email(email)

    @staticmethod
    def _validate_birthdate(birthdate: date) -> None:
        if birthdate > date.today():
            raise ValueError("birthdate cannot be in the future")
