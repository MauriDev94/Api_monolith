from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class Todo:
    """Mutable todo entity with invariants and explicit behavior methods."""

    id: str | None
    user_id: str
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.user_id = self._require_text(self.user_id, "user_id")
        self.title = self._require_text(self.title, "title")
        self.description = self._normalize_description(self.description)

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
        self.updated_at = datetime.now(timezone.utc)

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
