from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.providers.db import get_db_session
from app.features.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)


def get_notification_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> NotificationRepository:
    """Get notification repository instance."""
    return NotificationRepository(session=db_session)
