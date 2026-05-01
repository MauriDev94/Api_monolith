import httpx
from loguru import logger

from app.core.exceptions.exceptions import InternalServerError
from app.features.auth.application.contracts.email_sender import EmailSender

RESEND_API_URL = "https://api.resend.com/emails"

PURPOSE_SUBJECTS = {
    "password_change": "Reset your password — MauriDev API",
}

OTP_HTML_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
  <h2 style="color: #1a1a1a; margin-bottom: 8px;">Your verification code</h2>
  <p style="color: #555; margin-bottom: 24px;">{purpose_text}</p>
  <div style="background: #f4f4f4; border-radius: 8px; padding: 24px; text-align: center;">
    <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1a1a1a;">
      {code}
    </span>
  </div>
  <p style="color: #888; font-size: 13px; margin-top: 24px;">
    This code expires in 10 minutes. If you didn't request this, ignore this email.
  </p>
</div>
"""

PURPOSE_TEXT = {
    "password_change": "Use this code to reset your password.",
}


class ResendEmailSender(EmailSender):
    """Resend HTTP API implementation for sending transactional emails."""

    def __init__(self, api_key: str, sender_email: str):
        self.api_key = api_key
        self.sender_email = sender_email

    def send_otp(self, to_email: str, code: str, purpose: str) -> None:
        subject = PURPOSE_SUBJECTS.get(purpose, f"Your verification code — {purpose}")
        purpose_text = PURPOSE_TEXT.get(purpose, "Use this code to verify your identity.")
        html_body = OTP_HTML_TEMPLATE.format(code=code, purpose_text=purpose_text)

        try:
            response = httpx.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.sender_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Resend API error: {} {}", exc.response.status_code, exc.response.text)
            raise InternalServerError(
                f"resend api error: {exc.response.status_code} {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Resend connection error: {}", type(exc).__name__)
            raise InternalServerError("failed to connect to resend api") from exc
