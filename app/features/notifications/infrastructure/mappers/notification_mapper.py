from app.features.notifications.domain.entities.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from app.features.notifications.infrastructure.models.notification_model import NotificationModel


def map_notification_model_to_entity(model: NotificationModel) -> Notification:
    """Map ORM notification model to domain entity."""
    return Notification(
        id=model.id,
        user_id=model.user_id,
        type=NotificationType(model.type),
        title=model.title,
        message=model.message,
        related_entity_id=model.related_entity_id,
        status=NotificationStatus(model.status),
        sent_at=model.sent_at,
        read_at=model.read_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def map_notification_entity_to_model(
    model: NotificationModel, notification: Notification
) -> NotificationModel:
    """Apply domain notification state to an existing ORM model."""
    model.user_id = notification.user_id
    model.type = notification.type.value
    model.title = notification.title
    model.message = notification.message
    model.related_entity_id = notification.related_entity_id
    model.status = notification.status.value
    model.sent_at = notification.sent_at
    model.read_at = notification.read_at
    return model
