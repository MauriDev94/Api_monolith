import pytest

from app.features.users.domain.value_objects.email import Email


# Tipo de test: Unit
def test_should_normalize_email_value() -> None:
    """Valida que normaliza email valor."""
    email = Email("  USER@Mail.COM  ")

    assert email.value == "user@mail.com"
    assert str(email) == "user@mail.com"


@pytest.mark.parametrize(
    "raw_email",
    [
        "a.b-c_d@gmail.com",
        "user_name@hotmail.co",
        "x@outlook.cl",
    ],
)
# Tipo de test: Unit
def test_should_accept_valid_email_formats(raw_email: str) -> None:
    """Valida que acepta formatos válidos comunes."""
    assert Email(raw_email).value == raw_email.strip().lower()


@pytest.mark.parametrize(
    "raw_email",
    [
        "invalid-mail",
        "user@localhost",
        "@mail.com",
        "user@",
        ".user@mail.com",
        "user.@mail.com",
        "user..name@mail.com",
        "user@mail..com",
        "user@mail.c",
        "user@mail-domain.com",
        "user@mail1.com",
        "user+tag@mail.com",
        "user%name@mail.com",
        "user&name@mail.com",
        "user/name@mail.com",
        " ",
    ],
)
# Tipo de test: Unit
def test_should_raise_when_email_format_is_invalid(raw_email: str) -> None:
    """Valida que lanza cuando email formato es invalido."""
    with pytest.raises(ValueError, match="invalid email format"):
        Email(raw_email)
