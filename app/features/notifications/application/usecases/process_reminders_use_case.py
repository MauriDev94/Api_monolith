"""Background job para enviar recordatorios de TODOs pendientes."""

from datetime import UTC, datetime
from uuid import uuid4

from loguru import logger

from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.domain.entities.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from app.features.todos.application.contracts.todo_datasource import TodoDatasource


class ProcessRemindersUseCase:
    """Process pending reminders and create notifications."""

    def __init__(
        self,
        todo_datasource: TodoDatasource,
        notification_datasource: NotificationDatasource,
    ):
        self.todo_datasource = todo_datasource
        self.notification_datasource = notification_datasource

    def execute(self, days_ahead: int = 1) -> dict:
        """Process pending reminders y crea notificaciones.

        Returns:
            dict: {"processed": count, "created": count, "failed": count}
        """
        now = datetime.now(UTC)
        todos = self.todo_datasource.get_todos_with_upcoming_due_date(
            days_ahead=days_ahead,
            current_time=now,
        )

        created = 0
        failed = 0

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

                self.notification_datasource.create(notification)
                created += 1
                logger.info(f"Reminder created for todo {todo.id}")

            except Exception as e:
                failed += 1
                logger.error(f"Failed to create reminder for todo {todo.id}: {e}")

        return {"processed": len(todos), "created": created, "failed": failed}


def run_reminder_job() -> dict:
    """Entry point para el job de recordatorios (requires DI)."""
    logger.warning(
        "run_reminder_job() requires manual DI setup. "
        "Use ProcessRemindersUseCase with proper data sources."
    )
    return {"processed": 0, "created": 0, "failed": 0}
