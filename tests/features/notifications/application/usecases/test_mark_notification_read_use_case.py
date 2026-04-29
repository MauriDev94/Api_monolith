from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import ForbiddenError, NotFoundError
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.dto.mark_notification_read_params import (
    MarkNotificationReadParams,
)
from app.features.notifications.application.usecases.mark_notification_read_use_case import (
    MarkNotificationReadUseCase,
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
    status: NotificationStatus = NotificationStatus.SENT,
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
def test_should_mark_notification_as_read() -> None:
    """Valida que marca notificacion como leida exitosamente."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.SENT
    )
    updated_notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.READ
    )
    datasource.get_by_id.return_value = notification
    datasource.mark_as_read.return_value = updated_notification
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    result = use_case.execute(
        MarkNotificationReadParams(notification_id="notif-1", user_id="user-1")
    )

    datasource.get_by_id.assert_called_once_with("notif-1")
    datasource.mark_as_read.assert_called_once_with("notif-1")
    assert result.status == NotificationStatus.READ


# Tipo de test: Unit
def test_should_mark_notification_as_read_from_pending() -> None:
    """Valida que marca como leida直接从PENDING."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.PENDING
    )
    updated_notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.READ
    )
    datasource.get_by_id.return_value = notification
    datasource.mark_as_read.return_value = updated_notification
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    result = use_case.execute(
        MarkNotificationReadParams(notification_id="notif-1", user_id="user-1")
    )

    datasource.get_by_id.assert_called_once_with("notif-1")
    assert result.status == NotificationStatus.READ


# Tipo de test: Unit
def test_should_raise_not_found_when_notification_does_not_exist() -> None:
    """Valida que lanza error cuando la notificacion no existe."""
    datasource = Mock(spec=NotificationDatasource)
    datasource.get_by_id.return_value = None
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    with pytest.raises(NotFoundError, match="notification not found"):
        use_case.execute(
            MarkNotificationReadParams(notification_id="nonexistent", user_id="user-1")
        )


# Tipo de test: Unit
def test_should_raise_forbidden_when_user_is_not_owner() -> None:
    """Valida que lanza ForbiddenError cuando el usuario no es owner."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.SENT
    )
    datasource.get_by_id.return_value = notification
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    with pytest.raises(ForbiddenError, match="not authorized to modify this notification"):
        use_case.execute(MarkNotificationReadParams(notification_id="notif-1", user_id="user-2"))


# Tipo de test: Unit
def test_should_raise_when_notification_already_read() -> None:
    """Valida que intenta marcar como read cuando ya esta leida - el datasource lanza."""
    datasource = Mock(spec=NotificationDatasource)
    # La notificación ya está en READ
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
    # Cuando el datasource intenta marcar como read, lanza el erro
    datasource.mark_as_read.side_effect = ValueError("Cannot transition from read to read")
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    with pytest.raises(ValueError, match="Cannot transition from read to read"):
        use_case.execute(MarkNotificationReadParams(notification_id="notif-1", user_id="user-1"))


# Tipo de test: Unit
def test_should_raise_when_notification_failed() -> None:
    """Valida que intenta marcar como read cuando falló - el datasource lanza."""
    datasource = Mock(spec=NotificationDatasource)
    # La notificación está en FAILED - la creo directamente
    notification = Notification(
        id="notif-1",
        user_id="user-1",
        type=NotificationType.SYSTEM,
        title="Test Notification",
        message="Test message",
        related_entity_id=None,
        status=NotificationStatus.READ,
    )
    notification.status = NotificationStatus.FAILED
    datasource.get_by_id.return_value = notification
    # Cuando el datasource intenta marcar como read, lanza el error
    datasource.mark_as_read.side_effect = ValueError("Cannot transition from failed to read")
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    with pytest.raises(ValueError, match="Cannot transition from failed to read"):
        use_case.execute(MarkNotificationReadParams(notification_id="notif-1", user_id="user-1"))


# Tipo de test: Unit
def test_should_validate_ownership_before_marking_as_read() -> None:
    """Valida que el ownership es verificado antes de marcar como leida."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.SENT
    )
    datasource.get_by_id.return_value = notification
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    # Intentando con user diferente
    with pytest.raises(ForbiddenError):
        use_case.execute(MarkNotificationReadParams(notification_id="notif-1", user_id="user-999"))

    # No debe haber llamado a mark_as_read
    datasource.mark_as_read.assert_not_called()


# Tipo de test: Unit
def test_should_allow_owner_to_mark_sent_notification_as_read() -> None:
    """Valida que el owner puede marcar una notificacion enviada como leida."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.SENT
    )
    updated = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.READ
    )
    datasource.get_by_id.return_value = notification
    datasource.mark_as_read.return_value = updated
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    result = use_case.execute(
        MarkNotificationReadParams(notification_id="notif-1", user_id="user-1")
    )

    assert result.status == NotificationStatus.READ
    datasource.mark_as_read.assert_called_once_with("notif-1")


# Tipo de test: Unit
def test_should_allow_owner_to_mark_pending_notification_as_read() -> None:
    """Valida que el owner puede marcar una notificacion pendiente como leida."""
    datasource = Mock(spec=NotificationDatasource)
    notification = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.PENDING
    )
    updated = make_notification(
        notification_id="notif-1", user_id="user-1", status=NotificationStatus.READ
    )
    datasource.get_by_id.return_value = notification
    datasource.mark_as_read.return_value = updated
    use_case = MarkNotificationReadUseCase(notification_datasource=datasource)

    result = use_case.execute(
        MarkNotificationReadParams(notification_id="notif-1", user_id="user-1")
    )

    assert result.status == NotificationStatus.READ
