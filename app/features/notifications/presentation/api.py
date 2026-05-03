from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.config.env_config import EnvConfig
from app.core.providers.env_config import get_env_config
from app.core.router.router import get_versioned_router
from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.notifications.application.dto.get_notifications_params import (
    GetNotificationsParams,
)
from app.features.notifications.application.dto.mark_notification_read_params import (
    MarkNotificationReadParams,
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
from app.features.notifications.di.dependencies import (
    get_get_notifications_use_case,
    get_mark_notification_read_use_case,
    get_process_reminders_use_case,
)
from app.features.notifications.presentation.mappers.notification_mapper import (
    map_notification_entity_to_response,
)
from app.features.notifications.presentation.schemas.notification_schemas import (
    GetNotificationsResponse,
    MarkReadResponse,
)
from app.features.users.domain.entities.user import User


def _require_user_id(current_user: User) -> str:
    """Guarantee a non-empty authenticated user id."""
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return current_user.id


v1_router = get_versioned_router("v1")


@v1_router.get(
    "",
    response_model=GetNotificationsResponse,
    status_code=status.HTTP_200_OK,
)
def list_notifications(
    current_user: Annotated[User, Depends(get_authenticated_user)],
    use_case: Annotated[GetNotificationsUseCase, Depends(get_get_notifications_use_case)],
):
    """List all notifications for the authenticated user."""
    user_id = _require_user_id(current_user)
    notifications = use_case.execute(GetNotificationsParams(user_id=user_id))

    return GetNotificationsResponse(
        notifications=[map_notification_entity_to_response(n) for n in notifications]
    )


@v1_router.patch(
    "/{notification_id}/read",
    response_model=MarkReadResponse,
    status_code=status.HTTP_200_OK,
)
def mark_notification_as_read(
    notification_id: str,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    use_case: Annotated[MarkNotificationReadUseCase, Depends(get_mark_notification_read_use_case)],
):
    """Mark a notification as read."""
    user_id = _require_user_id(current_user)

    use_case.execute(MarkNotificationReadParams(notification_id=notification_id, user_id=user_id))

    return MarkReadResponse(message="Notification marked as read")


# Internal endpoint for cron-job.org (protected with X-Internal-Token)
@v1_router.post(
    "/internal/reminders/process",
    status_code=status.HTTP_200_OK,
)
def process_reminders(
    request: Request,
    use_case: Annotated[ProcessRemindersUseCase, Depends(get_process_reminders_use_case)],
    env_config: Annotated[EnvConfig, Depends(get_env_config)],
) -> dict:
    """Internal endpoint for cron-job.org to trigger reminder processing."""
    token = request.headers.get("X-Internal-Token")
    if not env_config.internal_api_key or token != env_config.internal_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = use_case.execute(days_ahead=1)
    return result
