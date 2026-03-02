from datetime import date

import pytest

from app.features.users.domain.value_objects.email import Email


def test_should_normalize_email_value() -> None:
    email = Email("  USER@Mail.COM  ")

    assert email.value == "user@mail.com"
    assert str(email) == "user@mail.com"


@pytest.mark.parametrize(
    "raw_email",
    [
        "invalid-mail",
        "user@localhost",
        "@mail.com",
        "user@",
    ],
)
def test_should_raise_when_email_format_is_invalid(raw_email: str) -> None:
    with pytest.raises(ValueError, match="invalid email format"):
        Email(raw_email)
