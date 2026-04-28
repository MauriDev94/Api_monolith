from app.common.use_case import UseCase
from app.core.exceptions.exceptions import NotFoundError
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.dto.set_notification_as_sent_params import (
    SetNotificationAsSentParams,
)
from app.features.notifications.domain.entities.notification import Notification


class SetNotificationAsSentUseCase(UseCase[SetNotificationAsSentParams, Notification]):
    """Mark a notification as sent (used by reminder orchestration)."""

    def __init__(self, notification_datasource: NotificationDatasource):
        self.notification_datasource = notification_datasource

    def execute(self, params: SetNotificationAsSentParams) -> Notification:
        """Mark a notification as sent."""
        notification = self.notification_datasource.get_by_id(params.notification_id)

        if notification is None:
            raise NotFoundError("notification not found")

        return self.notification_datasource.mark_as_sent(params.notification_id)
