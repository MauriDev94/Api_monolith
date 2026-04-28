from dataclasses import dataclass


@dataclass(slots=True)
class MarkNotificationReadParams:
    """Input DTO for marking a notification as read."""

    notification_id: str
    user_id: str  # owner for validation
