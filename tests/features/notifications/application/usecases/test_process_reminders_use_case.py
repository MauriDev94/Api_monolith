"""Tests unitarios para ProcessRemindersUseCase."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.notifications.application.contracts.notification_datasource import (
    NotificationDatasource,
)
from app.features.notifications.application.usecases.process_reminders_use_case import (
    ProcessRemindersUseCase,
)
from app.features.todos.application.contracts.todo_datasource import TodoDatasource
from app.features.users.domain.value_objects.email import Email


class TestProcessRemindersUseCase:
    """Test suite for ProcessRemindersUseCase."""

    @pytest.fixture
    def mock_todo_datasource(self):
        datasource = MagicMock(spec=TodoDatasource)
        datasource.get_todos_with_upcoming_due_date.return_value = []
        return datasource

    @pytest.fixture
    def mock_notification_datasource(self):
        datasource = MagicMock(spec=NotificationDatasource)
        datasource.create.return_value = MagicMock()
        datasource.mark_as_sent.return_value = MagicMock()
        return datasource

    @pytest.fixture
    def mock_auth_datasource(self):
        datasource = MagicMock(spec=AuthDatasource)
        return datasource

    @pytest.fixture
    def mock_email_sender(self):
        return MagicMock(spec=EmailSender)

    @pytest.fixture
    def use_case(
        self,
        mock_todo_datasource,
        mock_notification_datasource,
        mock_auth_datasource,
        mock_email_sender,
    ):
        return ProcessRemindersUseCase(
            todo_datasource=mock_todo_datasource,
            notification_datasource=mock_notification_datasource,
            auth_datasource=mock_auth_datasource,
            email_sender=mock_email_sender,
        )

    @pytest.fixture
    def sample_user(self):
        user = MagicMock()
        user.id = str(uuid4())
        user.email = Email("test@example.com")
        return user

    @pytest.fixture
    def sample_todo(self, sample_user):
        todo = MagicMock()
        todo.id = str(uuid4())
        todo.user_id = sample_user.id
        todo.title = "Estudiar Python"
        todo.due_date = datetime.now(UTC) + timedelta(days=1)
        return todo

    def test_should_send_email_and_mark_as_sent_when_todo_has_upcoming_due_date(
        self,
        use_case,
        mock_todo_datasource,
        mock_notification_datasource,
        mock_auth_datasource,
        mock_email_sender,
        sample_todo,
        sample_user,
    ):
        """Test: todo con due_date próximo, user existe, email OK → notificación SENT, sent=1."""
        mock_todo_datasource.get_todos_with_upcoming_due_date.return_value = [sample_todo]
        mock_auth_datasource.get_user_by_id.return_value = sample_user

        result = use_case.execute(days_ahead=1)

        assert result["processed"] == 1
        assert result["created"] == 1
        assert result["sent"] == 1
        assert result["failed"] == 0
        mock_email_sender.send_reminder.assert_called_once()
        mock_notification_datasource.mark_as_sent.assert_called_once()

    def test_should_leave_notification_pending_when_email_send_fails(
        self,
        use_case,
        mock_todo_datasource,
        mock_notification_datasource,
        mock_auth_datasource,
        mock_email_sender,
        sample_todo,
        sample_user,
    ):
        """Test: email_sender.send_reminder lanza excepción → notificación queda en PENDING, failed=1."""
        mock_todo_datasource.get_todos_with_upcoming_due_date.return_value = [sample_todo]
        mock_auth_datasource.get_user_by_id.return_value = sample_user
        mock_email_sender.send_reminder.side_effect = Exception("SMTP error")

        result = use_case.execute(days_ahead=1)

        assert result["processed"] == 1
        assert result["created"] == 1
        assert result["sent"] == 0
        assert result["failed"] == 1
        mock_notification_datasource.mark_as_sent.assert_not_called()

    def test_should_skip_todo_when_user_not_found(
        self,
        use_case,
        mock_todo_datasource,
        mock_notification_datasource,
        mock_auth_datasource,
        sample_todo,
    ):
        """Test: auth_datasource.get_user_by_id retorna None → failed=1, no crea notificación."""
        mock_todo_datasource.get_todos_with_upcoming_due_date.return_value = [sample_todo]
        mock_auth_datasource.get_user_by_id.return_value = None

        result = use_case.execute(days_ahead=1)

        assert result["processed"] == 1
        assert result["created"] == 0
        assert result["sent"] == 0
        assert result["failed"] == 1
        mock_notification_datasource.create.assert_not_called()

    def test_should_return_correct_counts(
        self,
        use_case,
        mock_todo_datasource,
        mock_notification_datasource,
        mock_auth_datasource,
        mock_email_sender,
        sample_user,
    ):
        """Test: 3 todos: 2 OK, 1 falla → processed=3, sent=2, failed=1."""
        todos = []
        for i in range(3):
            todo = MagicMock()
            todo.id = str(uuid4())
            todo.user_id = sample_user.id
            todo.title = f"Tarea {i + 1}"
            todo.due_date = datetime.now(UTC) + timedelta(days=1)
            todos.append(todo)

        mock_todo_datasource.get_todos_with_upcoming_due_date.return_value = todos
        mock_auth_datasource.get_user_by_id.return_value = sample_user
        # Make second todo fail
        mock_email_sender.send_reminder.side_effect = [None, Exception("Email failed"), None]

        result = use_case.execute(days_ahead=1)

        assert result["processed"] == 3
        assert result["sent"] == 2
        assert result["failed"] == 1

    def test_should_return_empty_counts_when_no_todos_due(self, use_case, mock_todo_datasource):
        """Test: get_todos_with_upcoming_due_date retorna [] → processed=0, created=0, sent=0, failed=0."""
        mock_todo_datasource.get_todos_with_upcoming_due_date.return_value = []

        result = use_case.execute(days_ahead=1)

        assert result["processed"] == 0
        assert result["created"] == 0
        assert result["sent"] == 0
        assert result["failed"] == 0

    def test_should_process_multiple_todos_independently(
        self,
        use_case,
        mock_todo_datasource,
        mock_notification_datasource,
        mock_auth_datasource,
        mock_email_sender,
        sample_user,
    ):
        """Test: cada todo se procesa de forma independiente, fallo en uno no afecta los demás."""
        todos = []
        for i in range(3):
            todo = MagicMock()
            todo.id = str(uuid4())
            todo.user_id = sample_user.id
            todo.title = f"Tarea {i + 1}"
            todo.due_date = datetime.now(UTC) + timedelta(days=1)
            todos.append(todo)

        mock_todo_datasource.get_todos_with_upcoming_due_date.return_value = todos
        mock_auth_datasource.get_user_by_id.return_value = sample_user

        result = use_case.execute(days_ahead=1)

        assert result["processed"] == 3
        assert result["created"] == 3
        assert result["sent"] == 3
        assert result["failed"] == 0
        assert mock_email_sender.send_reminder.call_count == 3
        assert mock_notification_datasource.mark_as_sent.call_count == 3
