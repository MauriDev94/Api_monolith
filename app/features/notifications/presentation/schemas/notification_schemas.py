from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateNotificationRequest(BaseModel):
    """Request schema for creating a notification (internal use)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str
    type: str
    title: str = Field(min_length=1, max_length=150)
    message: str
    related_entity_id: str | None = None


class NotificationResponse(BaseModel):
    """Response schema for notification."""

    id: str
    user_id: str
    type: str
    title: str
    message: str
    related_entity_id: str | None
    status: str
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class GetNotificationsResponse(BaseModel):
    """Response schema for list notifications endpoint."""

    notifications: list[NotificationResponse]


class MarkReadResponse(BaseModel):
    """Response schema for mark as read."""

    message: str
