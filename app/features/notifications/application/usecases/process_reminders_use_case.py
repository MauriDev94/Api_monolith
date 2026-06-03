"""Background job para enviar recordatorios de TODOs pendientes."""

from datetime import UTC, datetime

from loguru import logger

from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.domain.entities.notification import Notification
from app.features.todos.application.contracts.todo_datasource import TodoDatasource


class ProcessRemindersUseCase:
    """Process pending reminders, send emails and create notifications."""

    def __init__(
        self,
        todo_datasource: TodoDatasource,
        notification_datasource: NotificationDatasource,
        auth_datasource: AuthDatasource,
        email_sender: EmailSender,
    ):
        self.todo_datasource = todo_datasource
        self.notification_datasource = notification_datasource
        self.auth_datasource = auth_datasource
        self.email_sender = email_sender

    def execute(self, days_ahead: int = 1) -> dict:
        """Process pending reminders: crear notificaciones y enviar emails.

        Returns:
            dict: {"processed": count, "created": count, "sent": count, "failed": count}
        """
        now = datetime.now(UTC)
        todos = self.todo_datasource.get_todos_with_upcoming_due_date(
            days_ahead=days_ahead,
            current_time=now,
        )

        created = 0
        sent = 0
        failed = 0

        for todo in todos:
            try:
                if todo.id is None:
                    logger.warning("Skipping todo with missing id")
                    failed += 1
                    continue

                # 1. Obtener usuario
                user = self.auth_datasource.get_user_by_id(todo.user_id)
                if user is None:
                    logger.warning(f"User not found for todo {todo.id}, skipping")
                    failed += 1
                    continue

                # 2. Crear notificación en PENDING
                notification = Notification.create_for_todo_reminder(
                    user_id=todo.user_id,
                    todo_id=todo.id,
                    todo_title=todo.title,
                )
                saved_notification = self.notification_datasource.create(notification)
                created += 1

                # 3. Enviar email
                due_date_str = todo.due_date.strftime("%d/%m/%Y %H:%M") if todo.due_date else ""
                self.email_sender.send_reminder(
                    to_email=user.email.value,
                    todo_title=todo.title,
                    due_date=due_date_str,
                )

                # 4. Marcar como SENT
                if saved_notification.id is None:
                    raise ValueError("saved notification has no id")
                self.notification_datasource.mark_as_sent(saved_notification.id)
                sent += 1
                logger.info(f"Reminder sent for todo {todo.id}")

            except Exception as e:
                # Dejar en PENDING para reintento
                failed += 1
                logger.error(f"Failed to process reminder for todo {todo.id}: {e}")

        return {"processed": len(todos), "created": created, "sent": sent, "failed": failed}


def run_reminder_job() -> dict:
    """Entry point para el job de recordatorios (requires DI)."""
    logger.warning(
        "run_reminder_job() requires manual DI setup. "
        "Use ProcessRemindersUseCase with proper data sources."
    )
    return {"processed": 0, "created": 0, "sent": 0, "failed": 0}
