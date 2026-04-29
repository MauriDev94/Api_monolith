from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class NotificationType(Enum):
    """Types of notifications available in the system."""

    TODO_REMINDER = "todo_reminder"
    NEWSLETTER = "newsletter"
    SYSTEM = "system"


class NotificationStatus(Enum):
    """Status of a notification.

    Valid transitions:
    - PENDING -> SENT (send)
    - PENDING -> READ (direct read without sending)
    - SENT -> READ (read after sent)
    - Any -> FAILED (on error)
    """

    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"


# Valid state transitions
VALID_TRANSITIONS = {
    NotificationStatus.PENDING: {
        NotificationStatus.SENT,
        NotificationStatus.READ,
        NotificationStatus.FAILED,
    },
    NotificationStatus.SENT: {NotificationStatus.READ, NotificationStatus.FAILED},
    NotificationStatus.READ: set(),  # Terminal state - no transitions allowed
    NotificationStatus.FAILED: set(),  # Terminal state - no transitions allowed
}


@dataclass(slots=True)
class Notification:
    """Notification entity for user alerts and reminders.

    Invariants:
    - user_id, title, message cannot be empty
    - Status transitions are restricted (see VALID_TRANSITIONS)
    - read_at can only be set when status becomes READ
    - sent_at can only be set when status becomes SENT
    """

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
        self._validate_required_fields()
        self._validate_initial_state()

    def _validate_required_fields(self) -> None:
        """Validate required text fields are not empty."""
        self.user_id = self._require_text(self.user_id, "user_id")
        self.title = self._require_text(self.title, "title")
        self.message = self._require_text(self.message, "message")

    def _validate_initial_state(self) -> None:
        """Validate initial state is valid."""
        if self.status not in {NotificationStatus.PENDING, NotificationStatus.READ}:
            raise ValueError(f"Invalid initial status: {self.status}. Must be PENDING or READ")

    def _can_transition_to(self, new_status: NotificationStatus) -> bool:
        """Check if transition to new_status is valid."""
        return new_status in VALID_TRANSITIONS.get(self.status, set())

    def mark_as_sent(self) -> None:
        """Mark notification as sent.

        Valid from: PENDING
        Raises: ValueError if already sent or read
        """
        if not self._can_transition_to(NotificationStatus.SENT):
            raise ValueError(
                f"Cannot transition from {self.status.value} to sent. "
                f"Valid transitions: {VALID_TRANSITIONS.get(self.status, set())}"
            )
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now(UTC)
        self._mark_as_updated()

    def mark_as_read(self) -> None:
        """Mark notification as read.

        Valid from: PENDING, SENT
        Raises: ValueError if already read
        """
        if not self._can_transition_to(NotificationStatus.READ):
            raise ValueError(
                f"Cannot transition from {self.status.value} to read. "
                f"Valid transitions: {VALID_TRANSITIONS.get(self.status, set())}"
            )
        self.status = NotificationStatus.READ
        self.read_at = datetime.now(UTC)
        self._mark_as_updated()

    def mark_as_failed(self) -> None:
        """Mark notification as failed.

        Valid from: PENDING, SENT
        Raises: ValueError if already read or failed
        """
        if not self._can_transition_to(NotificationStatus.FAILED):
            raise ValueError(
                f"Cannot transition from {self.status.value} to failed. "
                f"Valid transitions: {VALID_TRANSITIONS.get(self.status, set())}"
            )
        self.status = NotificationStatus.FAILED
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

    # Query methods

    def is_pending(self) -> bool:
        """Check if notification is pending."""
        return self.status == NotificationStatus.PENDING

    def is_sent(self) -> bool:
        """Check if notification has been sent."""
        return self.status == NotificationStatus.SENT

    def is_read(self) -> bool:
        """Check if notification has been read."""
        return self.status == NotificationStatus.READ

    def is_failed(self) -> bool:
        """Check if notification failed to send."""
        return self.status == NotificationStatus.FAILED

    def can_be_read(self) -> bool:
        """Check if notification can transition to READ."""
        return self._can_transition_to(NotificationStatus.READ)
