from app.common.use_case import UseCase
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.dto.get_notifications_params import (
    GetNotificationsParams,
)
from app.features.notifications.domain.entities.notification import Notification


class GetNotificationsUseCase(UseCase[GetNotificationsParams, list[Notification]]):
    """Retrieve notifications for a user with optional filtering."""

    def __init__(self, notification_datasource: NotificationDatasource):
        self.notification_datasource = notification_datasource

    def execute(self, params: GetNotificationsParams) -> list[Notification]:
        """Return notifications for a user, ordered by created_at DESC."""
        if params.status is not None:
            return self.notification_datasource.get_notifications_by_user_and_status(
                user_id=params.user_id,
                status=params.status,
            )
        return self.notification_datasource.get_by_user(params.user_id)
