from unittest.mock import Mock

from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.dto.get_notifications_params import (
    GetNotificationsParams,
)
from app.features.notifications.application.usecases.get_notifications_use_case import (
    GetNotificationsUseCase,
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
def test_should_return_all_notifications_when_no_filter() -> None:
    """Valida que retorna todas las notificaciones sin filtro."""
    datasource = Mock(spec=NotificationDatasource)
    expected_notifications = [
        make_notification(notification_id="notif-1", status=NotificationStatus.PENDING),
        make_notification(notification_id="notif-2", status=NotificationStatus.SENT),
        make_notification(notification_id="notif-3", status=NotificationStatus.READ),
    ]
    datasource.get_by_user.return_value = expected_notifications
    use_case = GetNotificationsUseCase(notification_datasource=datasource)

    result = use_case.execute(GetNotificationsParams(user_id="user-1"))

    datasource.get_by_user.assert_called_once_with("user-1")
    assert len(result) == 3


# Tipo de test: Unit
def test_should_filter_by_status_pending() -> None:
    """Valida que filtra por estado PENDING."""
    datasource = Mock(spec=NotificationDatasource)
    pending_notifications = [
        make_notification(notification_id="notif-1", status=NotificationStatus.PENDING),
    ]
    datasource.get_notifications_by_user_and_status.return_value = pending_notifications
    use_case = GetNotificationsUseCase(notification_datasource=datasource)

    result = use_case.execute(
        GetNotificationsParams(user_id="user-1", status=NotificationStatus.PENDING)
    )

    datasource.get_notifications_by_user_and_status.assert_called_once_with(
        user_id="user-1", status=NotificationStatus.PENDING
    )
    assert len(result) == 1
    assert result[0].is_pending()


# Tipo de test: Unit
def test_should_filter_by_status_sent() -> None:
    """Valida que filtra por estado SENT."""
    datasource = Mock(spec=NotificationDatasource)
    sent_notifications = [
        make_notification(notification_id="notif-1", status=NotificationStatus.SENT),
    ]
    datasource.get_notifications_by_user_and_status.return_value = sent_notifications
    use_case = GetNotificationsUseCase(notification_datasource=datasource)

    result = use_case.execute(
        GetNotificationsParams(user_id="user-1", status=NotificationStatus.SENT)
    )

    datasource.get_notifications_by_user_and_status.assert_called_once_with(
        user_id="user-1", status=NotificationStatus.SENT
    )
    assert len(result) == 1
    assert result[0].is_sent()


# Tipo de test: Unit
def test_should_filter_by_status_read() -> None:
    """Valida que filtra por estado READ."""
    datasource = Mock(spec=NotificationDatasource)
    read_notifications = [
        make_notification(notification_id="notif-1", status=NotificationStatus.READ),
    ]
    datasource.get_notifications_by_user_and_status.return_value = read_notifications
    use_case = GetNotificationsUseCase(notification_datasource=datasource)

    result = use_case.execute(
        GetNotificationsParams(user_id="user-1", status=NotificationStatus.READ)
    )

    datasource.get_notifications_by_user_and_status.assert_called_once_with(
        user_id="user-1", status=NotificationStatus.READ
    )
    assert len(result) == 1
    assert result[0].is_read()


# Tipo de test: Unit
def test_should_return_empty_list_when_no_notifications() -> None:
    """Valida que retorna lista vacia cuando no hay notificaciones."""
    datasource = Mock(spec=NotificationDatasource)
    datasource.get_by_user.return_value = []
    use_case = GetNotificationsUseCase(notification_datasource=datasource)

    result = use_case.execute(GetNotificationsParams(user_id="user-1"))

    assert result == []


# Tipo de test: Unit
def test_should_return_empty_list_when_status_filter_matches_nothing() -> None:
    """Valida que retorna lista vacia cuando filtro no encuentra nada."""
    datasource = Mock(spec=NotificationDatasource)
    datasource.get_notifications_by_user_and_status.return_value = []
    use_case = GetNotificationsUseCase(notification_datasource=datasource)

    result = use_case.execute(
        GetNotificationsParams(user_id="user-1", status=NotificationStatus.READ)
    )

    assert result == []
