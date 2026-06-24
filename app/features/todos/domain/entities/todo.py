from dataclasses import dataclass
from datetime import UTC, datetime

from app.common.domain_error import DomainError


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
        self.due_date = self._normalize_due_date(self.due_date)

    @staticmethod
    def _normalize_due_date(due_date: datetime | None) -> datetime | None:
        """Garantiza que due_date sea timezone-aware.

        NO rechaza fechas pasadas: una entidad reconstruida desde la BD (p.ej. un
        todo ya vencido) siempre debe poder existir. La regla "no en el pasado" es
        de CREACIÓN, no un invariante permanente; se valida en el borde de entrada
        (schema del request) y en `set_due_date`.
        """
        if due_date is None:
            return None
        if due_date.tzinfo is None:
            return due_date.replace(tzinfo=UTC)
        return due_date

    def set_due_date(self, due_date: datetime | None) -> None:
        """Cambia el due_date rechazando fechas en el pasado (acción explícita)."""
        normalized = self._normalize_due_date(due_date)
        if normalized is not None and normalized < datetime.now(UTC):
            raise DomainError("due_date cannot be in the past")
        self.due_date = normalized
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
            raise DomainError(f"{field_name} cannot be empty")
        return normalized

    @staticmethod
    def _normalize_description(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
