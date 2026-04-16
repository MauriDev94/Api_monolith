"""Background job para enviar recordatorios de TODOs pendientes."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from loguru import logger
from sqlalchemy.orm import Session

from app.features.notifications.domain.entities.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from app.features.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.todos.infrastructure.models.todo_model import TodoModel


def get_pending_reminders(session: Session, days_ahead: int = 1) -> list[TodoModel]:
    """Get todos con due_date dentro de los próximos N días y no completados."""
    now = datetime.now(UTC)
    deadline = now + timedelta(days=days_ahead)

    return (
        session.query(TodoModel)
        .filter(
            TodoModel.due_date.isnot(None),
            TodoModel.due_date <= deadline,
            TodoModel.due_date >= now,
            TodoModel.is_completed.is_(False),
        )
        .all()
    )


def process_reminders(days_ahead: int = 1) -> dict:
    """Process pending reminders y crea notificaciones.

    Esta función está diseñada para ser llamada periódicamente (ej: via cron).

    Returns:
        dict: {"processed": count, "created": count, "failed": count}
    """
    from app.core.providers.db import get_db_session

    db_gen = get_db_session()
    session = next(db_gen)

    try:
        todos = get_pending_reminders(session, days_ahead)

        created = 0
        failed = 0

        notification_repo = NotificationRepository(session=session)

        for todo in todos:
            try:
                notification = Notification(
                    id=str(uuid4()),
                    user_id=todo.user_id,
                    type=NotificationType.TODO_REMINDER,
                    title="Recordatorio de Tarea",
                    message=f"Tu tarea '{todo.title}' vence pronto",
                    related_entity_id=todo.id,
                    status=NotificationStatus.PENDING,
                )

                notification_repo.save(notification)
                created += 1
                logger.info(f"Reminder created for todo {todo.id}")

            except Exception as e:
                failed += 1
                logger.error(f"Failed to create reminder for todo {todo.id}: {e}")

        return {"processed": len(todos), "created": created, "failed": failed}

    finally:
        try:
            next(db_gen, None)
        except StopIteration:
            pass


def run_reminder_job():
    """Entry point para el job de recordatorios."""
    logger.info("Running reminder job...")
    result = process_reminders(days_ahead=1)
    logger.info(f"Reminder job completed: {result}")
    return result


if __name__ == "__main__":
    run_reminder_job()
