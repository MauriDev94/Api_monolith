import pytest

from app.core.exceptions.exceptions import InternalServerError
from app.features.auth.infrastructure.providers.smtp_email_sender import SmtpEmailSender


class _FakeSmtpClient:
    def __init__(self):
        self.started_tls = False
        self.logged = False
        self.sent = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def starttls(self):
        self.started_tls = True

    def login(self, username: str, password: str):
        self.logged = bool(username) and bool(password)

    def send_message(self, _message):
        self.sent = True


# Tipo de test: Unit
def test_should_send_otp_email_via_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeSmtpClient()

    def fake_smtp(*_args, **_kwargs):
        return fake_client

    monkeypatch.setattr("smtplib.SMTP", fake_smtp)

    sender = SmtpEmailSender(
        host="smtp.test.local",
        port=587,
        username="user",
        password="pass",
        sender_email="noreply@test.local",
        use_tls=True,
    )

    sender.send_otp(to_email="mauri@mail.com", code="123456", purpose="login")

    assert fake_client.started_tls is True
    assert fake_client.logged is True
    assert fake_client.sent is True


# Tipo de test: Unit
def test_should_raise_internal_error_when_smtp_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_smtp(*_args, **_kwargs):
        raise OSError("smtp offline")

    monkeypatch.setattr("smtplib.SMTP", failing_smtp)

    sender = SmtpEmailSender(
        host="smtp.test.local",
        port=587,
        username="",
        password="",
        sender_email="noreply@test.local",
        use_tls=False,
    )

    with pytest.raises(InternalServerError, match="failed to send otp email"):
        sender.send_otp(to_email="mauri@mail.com", code="123456", purpose="login")
