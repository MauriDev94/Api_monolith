from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class Todo:
    """Mutable todo entity with invariants and explicit behavior methods."""

    id: str | None
    user_id: str
    title: str
    description: str | None
    is_completed: bool
    due_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.user_id = self._require_text(self.user_id, "user_id")
        self.title = self._require_text(self.title, "title")
        self.description = self._normalize_description(self.description)
        self.due_date = self._validate_due_date(self.due_date)

    def _validate_due_date(self, due_date: datetime | None) -> datetime | None:
        """Validate due_date: must be timezone-aware and not in the past."""
        if due_date is None:
            return None
        # Ensure timezone-aware
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=UTC)
        # Check not in the past (allow current time)
        now = datetime.now(UTC)
        if due_date < now:
            raise ValueError("due_date cannot be in the past")
        return due_date

    def set_due_date(self, due_date: datetime | None) -> None:
        """Set due_date with validation."""
        self.due_date = self._validate_due_date(due_date)
        self._mark_as_updated()

    def remove_due_date(self) -> None:
        """Remove due_date."""
        self.due_date = None
        self._mark_as_updated()

    def rename(self, new_title: str) -> None:
        """Rename todo title applying domain validation."""
        self.title = self._require_text(new_title, "title")
        self._mark_as_updated()

    def change_description(self, new_description: str | None) -> None:
        """Change todo description with normalization to None when blank."""
        self.description = self._normalize_description(new_description)
        self._mark_as_updated()

    def mark_completed(self) -> None:
        """Mark todo as completed."""
        self.is_completed = True
        self._mark_as_updated()

    def mark_pending(self) -> None:
        """Mark todo as pending."""
        self.is_completed = False
        self._mark_as_updated()

    def _mark_as_updated(self) -> None:
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} cannot be empty")
        return normalized

    @staticmethod
    def _normalize_description(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
