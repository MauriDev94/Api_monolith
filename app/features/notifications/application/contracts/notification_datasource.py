from abc import ABC, abstractmethod

from app.features.notifications.domain.entities.notification import (
    Notification,
    NotificationStatus,
)


class NotificationDatasource(ABC):
    """Application port that defines persistence operations for notifications."""

    @abstractmethod
    def get_by_user(self, user_id: str) -> list[Notification]:
        """Return all notifications for a user, ordered by created_at DESC."""
        pass

    @abstractmethod
    def get_by_id(self, notification_id: str) -> Notification | None:
        """Return a notification by id or None when it does not exist."""
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: str) -> Notification:
        """Mark a notification as read and return the updated entity."""
        pass

    @abstractmethod
    def create(self, notification: Notification) -> Notification:
        """Persist a new notification and return the created entity."""
        pass

    @abstractmethod
    def get_notifications_by_user_and_status(
        self, user_id: str, status: NotificationStatus | None = None
    ) -> list[Notification]:
        """Return notifications filtered by user and optionally by status."""
        pass

    @abstractmethod
    def mark_as_sent(self, notification_id: str) -> Notification:
        """Mark a notification as sent and return the updated entity."""
        pass
