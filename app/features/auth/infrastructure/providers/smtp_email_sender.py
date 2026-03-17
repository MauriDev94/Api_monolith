import smtplib
from email.message import EmailMessage

from app.core.exceptions.exceptions import InternalServerError
from app.features.auth.application.contracts.email_sender import EmailSender


class SmtpEmailSender(EmailSender):
    """SMTP implementation for sending OTP emails."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender_email: str,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender_email = sender_email
        self.use_tls = use_tls

    def send_otp(self, to_email: str, code: str, purpose: str) -> None:
        message = EmailMessage()
        message["Subject"] = f"Your OTP code for {purpose}"
        message["From"] = self.sender_email
        message["To"] = to_email
        message.set_content(f"Your OTP code is: {code}")

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as client:
                if self.use_tls:
                    client.starttls()
                if self.username:
                    client.login(self.username, self.password)
                client.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise InternalServerError("failed to send otp email") from exc
