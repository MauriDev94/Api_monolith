from app.features.notifications.domain.entities.notification import Notification
from app.features.notifications.presentation.schemas.notification_schemas import (
    NotificationResponse,
)


def map_notification_entity_to_response(notification: Notification) -> NotificationResponse:
    """Map notification entity to response schema."""
    return NotificationResponse(
        id=notification.id or "",
        user_id=notification.user_id,
        type=notification.type.value,
        title=notification.title,
        message=notification.message,
        related_entity_id=notification.related_entity_id,
        status=notification.status.value,
        sent_at=notification.sent_at,
        read_at=notification.read_at,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )
