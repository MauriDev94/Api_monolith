import pytest

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
    """Factory para crear Notification en diferentes estados."""
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
def test_should_transition_from_pending_to_sent() -> None:
    """Valida transicion valida de PENDING a SENT."""
    notification = make_notification(status=NotificationStatus.PENDING)

    notification.mark_as_sent()

    assert notification.status == NotificationStatus.SENT
    assert notification.sent_at is not None


# Tipo de test: Unit
def test_should_transition_from_pending_to_read() -> None:
    """Valida transicion valida de PENDING a READ."""
    notification = make_notification(status=NotificationStatus.PENDING)

    notification.mark_as_read()

    assert notification.status == NotificationStatus.READ
    assert notification.read_at is not None


# Tipo de test: Unit
def test_should_transition_from_sent_to_read() -> None:
    """Valida transicion valida de SENT a READ."""
    notification = make_notification(status=NotificationStatus.SENT)

    notification.mark_as_read()

    assert notification.status == NotificationStatus.READ
    assert notification.read_at is not None


# Tipo de test: Unit
def test_should_raise_when_transitioning_from_read_to_sent() -> None:
    """Valida que transition de READ a SENT lanza error."""
    notification = make_notification(status=NotificationStatus.READ)

    with pytest.raises(ValueError, match="Cannot transition from read to sent"):
        notification.mark_as_sent()


# Tipo de test: Unit
def test_should_raise_when_transitioning_from_read_to_pending() -> None:
    """Valida que no se puede volver de READ a PENDING."""
    notification = make_notification(status=NotificationStatus.READ)

    with pytest.raises(ValueError, match="Cannot transition from read"):
        notification.mark_as_sent()


# Tipo de test: Unit
def test_should_raise_when_transitioning_from_failed_to_any() -> None:
    """Valida que FAILED es estado terminal."""
    notification = make_notification(status=NotificationStatus.FAILED)

    with pytest.raises(ValueError, match="Cannot transition from failed"):
        notification.mark_as_sent()


# Tipo de test: Unit
def test_should_return_pending_status() -> None:
    """Valida que is_pending() retorna true para PENDING."""
    notification = make_notification(status=NotificationStatus.PENDING)

    assert notification.is_pending() is True
    assert notification.is_sent() is False
    assert notification.is_read() is False
    assert notification.is_failed() is False


# Tipo de test: Unit
def test_should_return_sent_status() -> None:
    """Valida que is_sent() retorna true para SENT."""
    notification = make_notification(status=NotificationStatus.SENT)

    assert notification.is_pending() is False
    assert notification.is_sent() is True
    assert notification.is_read() is False
    assert notification.is_failed() is False


# Tipo de test: Unit
def test_should_return_read_status() -> None:
    """Valida que is_read() retorna true para READ."""
    notification = make_notification(status=NotificationStatus.READ)

    assert notification.is_pending() is False
    assert notification.is_sent() is False
    assert notification.is_read() is True
    assert notification.is_failed() is False


# Tipo de test: Unit
def test_should_return_failed_status() -> None:
    """Valida que is_failed() retorna true para FAILED."""
    notification = make_notification(status=NotificationStatus.FAILED)

    assert notification.is_pending() is False
    assert notification.is_sent() is False
    assert notification.is_read() is False
    assert notification.is_failed() is True


# Tipo de test: Unit
def test_should_allow_read_from_pending() -> None:
    """Valida que can_be_read() retorna true para PENDING."""
    notification = make_notification(status=NotificationStatus.PENDING)

    assert notification.can_be_read() is True


# Tipo de test: Unit
def test_should_allow_read_from_sent() -> None:
    """Valida que can_be_read() retorna true para SENT."""
    notification = make_notification(status=NotificationStatus.SENT)

    assert notification.can_be_read() is True


# Tipo de test: Unit
def test_should_not_allow_read_from_read() -> None:
    """Valida que can_be_read() retorna false para READ (ya leida)."""
    notification = make_notification(status=NotificationStatus.READ)

    assert notification.can_be_read() is False


# Tipo de test: Unit
def test_should_not_allow_read_from_failed() -> None:
    """Valida que can_be_read() retorna false para FAILED."""
    notification = make_notification(status=NotificationStatus.FAILED)

    assert notification.can_be_read() is False


# Tipo de test: Unit
def test_should_normalize_text_fields() -> None:
    """Valida que normaliza campos de texto al crear."""
    notification = Notification(
        id="notif-1",
        user_id="  user-1  ",
        type=NotificationType.SYSTEM,
        title="  Test Title  ",
        message="  Test message  ",
        related_entity_id=None,
        status=NotificationStatus.PENDING,
    )

    assert notification.user_id == "user-1"
    assert notification.title == "Test Title"
    assert notification.message == "Test message"


# Tipo de test: Unit
def test_should_raise_when_user_id_is_empty() -> None:
    """Valida que lanza error cuando user_id esta vacio."""
    with pytest.raises(ValueError, match="user_id cannot be empty"):
        Notification(
            id="notif-1",
            user_id="   ",
            type=NotificationType.SYSTEM,
            title="Test Title",
            message="Test message",
            related_entity_id=None,
            status=NotificationStatus.PENDING,
        )


# Tipo de test: Unit
def test_should_raise_when_title_is_empty() -> None:
    """Valida que lanza error cuando title esta vacio."""
    with pytest.raises(ValueError, match="title cannot be empty"):
        Notification(
            id="notif-1",
            user_id="user-1",
            type=NotificationType.SYSTEM,
            title="   ",
            message="Test message",
            related_entity_id=None,
            status=NotificationStatus.PENDING,
        )


# Tipo de test: Unit
def test_should_raise_when_message_is_empty() -> None:
    """Valida que lanza error cuando message esta vacio."""
    with pytest.raises(ValueError, match="message cannot be empty"):
        Notification(
            id="notif-1",
            user_id="user-1",
            type=NotificationType.SYSTEM,
            title="Test Title",
            message="   ",
            related_entity_id=None,
            status=NotificationStatus.PENDING,
        )


# Tipo de test: Unit
def test_should_create_for_todo_reminder() -> None:
    """Valida el factory method para reminders."""
    notification = Notification.create_for_todo_reminder(
        user_id="user-1",
        todo_id="todo-123",
        todo_title="Buy milk",
    )

    assert notification.user_id == "user-1"
    assert notification.type == NotificationType.TODO_REMINDER
    assert notification.title == "Recordatorio de Tarea"
    assert "Buy milk" in notification.message
    assert notification.related_entity_id == "todo-123"
    assert notification.status == NotificationStatus.PENDING


# Tipo de test: Unit
def test_should_allow_any_status_when_reconstructed_from_db() -> None:
    """Valida que cuando id está setteado (simula DB), cualquier estado es válido."""
    # Simula reconstruir entidad desde la DB con estado SENT
    notification = Notification(
        id="notif-1",  # id setteado = viene de DB
        user_id="user-1",
        type=NotificationType.TODO_REMINDER,
        title="Test",
        message="Test message",
        related_entity_id="todo-1",
        status=NotificationStatus.SENT,  # Estado de la DB
    )
    assert notification.status == NotificationStatus.SENT


def test_should_raise_when_initial_status_is_invalid() -> None:
    """Valida que lanza error para estado inicial invalido (SENT).

    Nota: Solo aplica para nuevas entidades (id=None).
    Cuando id está setteado, se considera que viene de la DB.
    """
    with pytest.raises(ValueError, match="Invalid initial status"):
        Notification(
            id=None,  # Nueva notificación
            user_id="user-1",
            type=NotificationType.SYSTEM,
            title="Test Title",
            message="Test message",
            related_entity_id=None,
            status=NotificationStatus.SENT,  # No valido como inicial
        )


# Tipo de test: Unit
def test_should_allow_read_as_initial_status() -> None:
    """Valida READ como estado valido inicial (para migraciones)."""
    notification = Notification(
        id="notif-1",
        user_id="user-1",
        type=NotificationType.SYSTEM,
        title="Test Title",
        message="Test message",
        related_entity_id=None,
        status=NotificationStatus.READ,
    )

    assert notification.status == NotificationStatus.READ
    assert notification.is_read() is True
