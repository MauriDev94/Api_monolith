from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.notifications.di.dependencies import get_notification_repository
from app.features.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
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


v1_router = APIRouter(prefix="/notifications", tags=["v1 Notifications"])


@v1_router.get(
    "",
    response_model=GetNotificationsResponse,
    status_code=status.HTTP_200_OK,
)
def list_notifications(
    current_user: Annotated[User, Depends(get_authenticated_user)],
    repository: Annotated[NotificationRepository, Depends(get_notification_repository)],
):
    """List all notifications for the authenticated user."""
    user_id = _require_user_id(current_user)
    notifications = repository.find_by_user(user_id)

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
    repository: Annotated[NotificationRepository, Depends(get_notification_repository)],
):
    """Mark a notification as read."""
    user_id = _require_user_id(current_user)

    notification = repository.get_by_id(notification_id)

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    if notification.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    repository.mark_as_read(notification_id)

    return MarkReadResponse(message="Notification marked as read")
