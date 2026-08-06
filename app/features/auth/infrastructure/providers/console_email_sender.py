from app.features.auth.application.contracts.email_sender import EmailSender


class ConsoleEmailSender(EmailSender):
    """Console-based email sender for local testing."""

    def send_otp(self, to_email: str, code: str, purpose: str) -> None:
        print(f"[OTP] to={to_email} purpose={purpose} code={code}")
