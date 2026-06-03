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

    def mark_as_sent(self, notification_id: str) -> Notification:
        """Mark a notification as sent and return the updated entity."""
        ...

    def mark_as_read(self, notification_id: str) -> Notification:
        """Mark a notification as read and return the updated entity."""
        ...

    def get_by_id(self, notification_id: str) -> Notification | None:
        """Get a notification by ID."""
        ...
