from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Todo:
    """Immutable todo entity with basic invariants."""

    id: str | None
    user_id: str
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_id", self._require_text(self.user_id, "user_id"))
        object.__setattr__(self, "title", self._require_text(self.title, "title"))
        object.__setattr__(self, "description", self._normalize_description(self.description))

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
