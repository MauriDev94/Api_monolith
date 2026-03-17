from abc import ABC, abstractmethod


class EmailSender(ABC):
    """Application port for sending transactional emails."""

    @abstractmethod
    def send_otp(self, to_email: str, code: str, purpose: str) -> None:
        """Send a one-time password to the user."""
        pass
