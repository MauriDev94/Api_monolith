from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ForbiddenError, NotFoundError
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.dto.mark_notification_read_params import (
    MarkNotificationReadParams,
)
from app.features.notifications.domain.entities.notification import Notification


class MarkNotificationReadUseCase(UseCase[MarkNotificationReadParams, Notification]):
    """Mark a notification as read with ownership validation."""

    def __init__(self, notification_datasource: NotificationDatasource):
        self.notification_datasource = notification_datasource

    def execute(self, params: MarkNotificationReadParams) -> Notification:
        """Mark a notification as read if owned by the requesting user."""
        notification = self.notification_datasource.get_by_id(params.notification_id)

        if notification is None:
            raise NotFoundError("notification not found")

        if notification.user_id != params.user_id:
            raise ForbiddenError("not authorized to modify this notification")

        return self.notification_datasource.mark_as_read(params.notification_id)
