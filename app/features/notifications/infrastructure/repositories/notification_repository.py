from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import DatabaseException
from app.features.notifications.application.contracts.notification_store import NotificationStore
from app.features.notifications.domain.entities.notification import Notification, NotificationStatus
from app.features.notifications.infrastructure.mappers.notification_mapper import (
    map_notification_model_to_entity,
)
from app.features.notifications.infrastructure.models.notification_model import NotificationModel


class NotificationRepository(NotificationStore):
    """SQLAlchemy implementation for notification persistence."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, notification: Notification) -> Notification:
        if notification.id is None:
            notification.id = str(uuid4())

        try:
            model = NotificationModel(
                id=notification.id,
                user_id=notification.user_id,
                type=notification.type.value,
                title=notification.title,
                message=notification.message,
                related_entity_id=notification.related_entity_id,
                status=notification.status.value,
                sent_at=notification.sent_at,
                read_at=notification.read_at,
                created_at=notification.created_at or datetime.now(UTC),
                updated_at=notification.updated_at or datetime.now(UTC),
            )
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseException("failed to save notification") from exc

        return map_notification_model_to_entity(model)

    def find_by_user(self, user_id: str) -> list[Notification]:
        try:
            models = (
                self.session.query(NotificationModel)
                .filter(NotificationModel.user_id == user_id)
                .order_by(NotificationModel.created_at.desc())
                .all()
            )
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve notifications") from exc

        return [map_notification_model_to_entity(m) for m in models]

    def find_pending(self, before: datetime) -> list[Notification]:
        try:
            models = (
                self.session.query(NotificationModel)
                .filter(
                    NotificationModel.status == NotificationStatus.PENDING.value,
                    NotificationModel.created_at <= before,
                )
                .all()
            )
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve pending notifications") from exc

        return [map_notification_model_to_entity(m) for m in models]

    def mark_as_sent(self, notification_id: str) -> None:
        try:
            model = (
                self.session.query(NotificationModel)
                .filter(NotificationModel.id == notification_id)
                .first()
            )
            if model:
                model.status = NotificationStatus.SENT.value
                model.sent_at = datetime.now(UTC)
                self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseException("failed to mark notification as sent") from exc

    def mark_as_read(self, notification_id: str) -> None:
        try:
            model = (
                self.session.query(NotificationModel)
                .filter(NotificationModel.id == notification_id)
                .first()
            )
            if model:
                model.status = NotificationStatus.READ.value
                model.read_at = datetime.now(UTC)
                self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseException("failed to mark notification as read") from exc

    def get_by_id(self, notification_id: str) -> Notification | None:
        try:
            model = (
                self.session.query(NotificationModel)
                .filter(NotificationModel.id == notification_id)
                .first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve notification") from exc

        if model is None:
            return None
        return map_notification_model_to_entity(model)
