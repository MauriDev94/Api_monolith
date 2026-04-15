from datetime import datetime
from typing import Protocol

from app.features.notifications.domain.entities.notification import Notification


class NotificationStore(Protocol):
    """Contract for notification persistence operations."""

    def save(self, notification: Notification) -> Notification:
        """Save a notification to storage."""
        ...

    def find_by_user(self, user_id: str) -> list[Notification]:
        """Get all notifications for a user."""
        ...

    def find_pending(self, before: datetime) -> list[Notification]:
        """Get pending notifications that should be sent."""
        ...

    def mark_as_sent(self, notification_id: str) -> None:
        """Mark a notification as sent."""
        ...

    def mark_as_read(self, notification_id: str) -> None:
        """Mark a notification as read."""
        ...

    def get_by_id(self, notification_id: str) -> Notification | None:
        """Get a notification by ID."""
        ...
