from dataclasses import dataclass

from app.features.notifications.domain.entities.notification import NotificationStatus


@dataclass(slots=True)
class GetNotificationsParams:
    """Input DTO for retrieving notifications."""

    user_id: str
    status: NotificationStatus | None = None  # optional filter
    limit: int = 50  # default pagination
    offset: int = 0  # default offset
