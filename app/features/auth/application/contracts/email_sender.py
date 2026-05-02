from abc import ABC, abstractmethod


class EmailSender(ABC):
    """Application port for sending transactional emails."""

    @abstractmethod
    def send_otp(self, to_email: str, code: str, purpose: str) -> None:
        """Send a one-time password to the user."""
        pass

    @abstractmethod
    def send_reminder(self, to_email: str, todo_title: str, due_date: str) -> None:
        """Send a todo reminder email to the user."""
        pass
