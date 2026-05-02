from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.providers.db import get_db_session
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.auth.di.dependencies import get_auth_repository, get_email_sender
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.usecases.get_notifications_use_case import (
    GetNotificationsUseCase,
)
from app.features.notifications.application.usecases.mark_notification_read_use_case import (
    MarkNotificationReadUseCase,
)
from app.features.notifications.application.usecases.process_reminders_use_case import (
    ProcessRemindersUseCase,
)
from app.features.notifications.application.usecases.set_notification_as_sent_use_case import (
    SetNotificationAsSentUseCase,
)
from app.features.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.todos.di.dependencies import get_todo_repository


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


def get_process_reminders_use_case(
    todo_datasource: Annotated[AuthDatasource, Depends(get_todo_repository)],
    notification_datasource: Annotated[
        NotificationDatasource, Depends(get_notification_datasource)
    ],
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> ProcessRemindersUseCase:
    """Provide ProcessRemindersUseCase use case with all dependencies."""
    return ProcessRemindersUseCase(
        todo_datasource=todo_datasource,
        notification_datasource=notification_datasource,
        auth_datasource=auth_datasource,
        email_sender=email_sender,
    )
