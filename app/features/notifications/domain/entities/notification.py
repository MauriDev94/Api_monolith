from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class NotificationType(Enum):
    """Types of notifications available in the system."""

    TODO_REMINDER = "todo_reminder"
    NEWSLETTER = "newsletter"
    SYSTEM = "system"


class NotificationStatus(Enum):
    """Status of a notification."""

    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"


@dataclass(slots=True)
class Notification:
    """Notification entity for user alerts and reminders."""

    id: str | None
    user_id: str
    type: NotificationType
    title: str
    message: str
    related_entity_id: str | None  # e.g., todo_id for reminders
    status: NotificationStatus
    sent_at: datetime | None = None
    read_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.user_id = self._require_text(self.user_id, "user_id")
        self.title = self._require_text(self.title, "title")
        self.message = self._require_text(self.message, "message")

    def mark_as_sent(self) -> None:
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now(UTC)
        self._mark_as_updated()

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.status = NotificationStatus.READ
        self.read_at = datetime.now(UTC)
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
    def create_for_todo_reminder(
        user_id: str,
        todo_id: str,
        todo_title: str,
    ) -> "Notification":
        """Factory method to create a todo reminder notification."""
        return Notification(
            id=None,
            user_id=user_id,
            type=NotificationType.TODO_REMINDER,
            title="Recordatorio de Tarea",
            message=f"Tu tarea '{todo_title}' vence pronto",
            related_entity_id=todo_id,
            status=NotificationStatus.PENDING,
        )
