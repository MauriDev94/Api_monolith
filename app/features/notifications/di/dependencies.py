from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.providers.db import get_db_session
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.usecases.get_notifications_use_case import (
    GetNotificationsUseCase,
)
from app.features.notifications.application.usecases.mark_notification_read_use_case import (
    MarkNotificationReadUseCase,
)
from app.features.notifications.application.usecases.set_notification_as_sent_use_case import (
    SetNotificationAsSentUseCase,
)
from app.features.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)


def get_notification_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> NotificationRepository:
    """Get notification repository instance."""
    return NotificationRepository(session=db_session)


def get_notification_datasource(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> NotificationDatasource:
    """Provide SQLAlchemy-backed datasource for notification use cases."""
    return NotificationRepository(session=db_session)


def get_get_notifications_use_case(
    notification_datasource: Annotated[
        NotificationDatasource, Depends(get_notification_datasource)
    ],
) -> GetNotificationsUseCase:
    """Provide GetNotificationsUseCase use case."""
    return GetNotificationsUseCase(notification_datasource=notification_datasource)


def get_mark_notification_read_use_case(
    notification_datasource: Annotated[
        NotificationDatasource, Depends(get_notification_datasource)
    ],
) -> MarkNotificationReadUseCase:
    """Provide MarkNotificationReadUseCase use case."""
    return MarkNotificationReadUseCase(notification_datasource=notification_datasource)


def get_set_notification_as_sent_use_case(
    notification_datasource: Annotated[
        NotificationDatasource, Depends(get_notification_datasource)
    ],
) -> SetNotificationAsSentUseCase:
    """Provide SetNotificationAsSentUseCase use case."""
    return SetNotificationAsSentUseCase(notification_datasource=notification_datasource)
