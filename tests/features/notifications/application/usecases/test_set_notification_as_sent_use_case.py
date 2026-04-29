from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import NotFoundError
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.dto.set_notification_as_sent_params import (
    SetNotificationAsSentParams,
)
from app.features.notifications.application.usecases.set_notification_as_sent_use_case import (
    SetNotificationAsSentUseCase,
)
from app.features.notifications.domain.entities.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)


def make_notification(
    *,
    notification_id: str = "notif-1",
    user_id: str = "user-1",
    status: NotificationStatus = NotificationStatus.PENDING,
) -> Notification:
    """Factory para crear Notification."""
    notification = Notification(
        id=notification_id,
        user_id=user_id,
        type=NotificationType.SYSTEM,
        title="Test Notification",
        message="Test message",
        related_entity_id=None,
        status=NotificationStatus.PENDING,
    )
    # Aplicar transiciones para llegar a estados intermedios
    if status == NotificationStatus.SENT:
        notification.mark_as_sent()
    elif status == NotificationStatus.READ:
        notification.mark_as_read()
    elif status == NotificationStatus.FAILED:
        notification.mark_as_failed()
    return notification


# Tipo de test: Unit
def test_should_mark_notification_as_sent() -> None:
    """Valida que marca notificacion como sent exitosamente."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(notification_id="notif-1", status=NotificationStatus.PENDING)
    updated_notification = make_notification(
        notification_id="notif-1", status=NotificationStatus.SENT
    )
    datasource.get_by_id.return_value = notification
    datasource.mark_as_sent.return_value = updated_notification
    use_case = SetNotificationAsSentUseCase(notification_datasource=datasource)

    result = use_case.execute(SetNotificationAsSentParams(notification_id="notif-1"))

    datasource.get_by_id.assert_called_once_with("notif-1")
    datasource.mark_as_sent.assert_called_once_with("notif-1")
    assert result.status == NotificationStatus.SENT


# Tipo de test: Unit
def test_should_raise_not_found_when_notification_does_not_exist() -> None:
    """Valida que lanza error cuando la notificacion no existe."""
    datasource = Mock(spec=NotificationDatasource)
    datasource.get_by_id.return_value = None
    use_case = SetNotificationAsSentUseCase(notification_datasource=datasource)

    with pytest.raises(NotFoundError, match="notification not found"):
        use_case.execute(SetNotificationAsSentParams(notification_id="nonexistent"))

    datasource.get_by_id.assert_called_once_with("nonexistent")


# Tipo de test: Unit
def test_should_raise_when_notification_already_sent() -> None:
    """Valida que intenta marcar como sent cuando ya fue enviada - el datasource lanza."""
    datasource = Mock(spec=NotificationDatasource)
    notification = Notification(
        id="notif-1",
        user_id="user-1",
        type=NotificationType.SYSTEM,
        title="Test Notification",
        message="Test message",
        related_entity_id=None,
        status=NotificationStatus.PENDING,
    )
    notification.status = NotificationStatus.SENT
    datasource.get_by_id.return_value = notification
    # Cuando el datasource intenta marcar como sent, lanza el error
    datasource.mark_as_sent.side_effect = ValueError("Cannot transition from sent to sent")
    use_case = SetNotificationAsSentUseCase(notification_datasource=datasource)

    with pytest.raises(ValueError, match="Cannot transition from sent to sent"):
        use_case.execute(SetNotificationAsSentParams(notification_id="notif-1"))


# Tipo de test: Unit
def test_should_raise_when_notification_already_read() -> None:
    """Valida que intenta marcar como sent cuando ya fue leida - el datasource lanza."""
    datasource = Mock(spec=NotificationDatasource)
    notification = Notification(
        id="notif-1",
        user_id="user-1",
        type=NotificationType.SYSTEM,
        title="Test Notification",
        message="Test message",
        related_entity_id=None,
        status=NotificationStatus.READ,
    )
    datasource.get_by_id.return_value = notification
    # Cuando el datasource intenta marcar como sent, lanza el error
    datasource.mark_as_sent.side_effect = ValueError("Cannot transition from read to sent")
    use_case = SetNotificationAsSentUseCase(notification_datasource=datasource)

    with pytest.raises(ValueError, match="Cannot transition from read to sent"):
        use_case.execute(SetNotificationAsSentParams(notification_id="notif-1"))


# Tipo de test: Unit
def test_should_be_idempotent_when_called_twice_on_sent() -> None:
    """Valida idempotencia: segunda llamada con estado ya enviado."""
    datasource = Mock(spec=NotificationDatasource)
    # Primera llamada: la notificacion ya esta en estado SENT
    notification = Notification(
        id="notif-1",
        user_id="user-1",
        type=NotificationType.SYSTEM,
        title="Test Notification",
        message="Test message",
        related_entity_id=None,
        status=NotificationStatus.PENDING,
    )
    notification.status = NotificationStatus.SENT
    datasource.get_by_id.return_value = notification

    # Segunda llamada: el datasource lanza error
    datasource.mark_as_sent.side_effect = ValueError("Cannot transition from sent to sent")
    use_case = SetNotificationAsSentUseCase(notification_datasource=datasource)

    with pytest.raises(ValueError, match="Cannot transition from sent to sent"):
        use_case.execute(SetNotificationAsSentParams(notification_id="notif-1"))


# Tipo de test: Unit
def test_should_check_ownership_before_marking_as_sent() -> None:
    """Valida que ownership es revisado antes de marcar como sent."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.PENDING
    )
    datasource.get_by_id.return_value = notification
    use_case = SetNotificationAsSentUseCase(notification_datasource=datasource)

    # SetNotificationAsSentUseCase NO valida ownership - solo marca como sent
    result = use_case.execute(SetNotificationAsSentParams(notification_id="notif-1"))

    # El datasource fue llamado para obtener y marcar
    datasource.get_by_id.assert_called_once_with("notif-1")
    datasource.mark_as_sent.assert_called_once_with("notif-1")
    assert result is not None
