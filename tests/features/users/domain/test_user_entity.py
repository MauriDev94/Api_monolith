from datetime import date, timedelta

import pytest

from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


# Tipo de test: Unit
def test_should_normalize_user_text_fields_and_email() -> None:
    """Valida que normaliza usuario texto campos y correo."""
    user = User(
        id="user-1",
        name="  Mauri ",
        lastname=" Salinas  ",
        email=" MAURI@mail.com ",
        password_hash=" hash ",
        birthdate=date(2000, 1, 1),
    )

    assert user.name == "Mauri"
    assert user.lastname == "Salinas"
    assert user.email.value == "mauri@mail.com"
    assert user.password_hash == "hash"


@pytest.mark.parametrize("field, value", [("name", "   "), ("lastname", ""), ("password_hash", " ")])
# Tipo de test: Unit
def test_should_raise_when_required_user_text_field_is_empty(field: str, value: str) -> None:
    """Valida que lanza cuando requerido usuario texto campo es vacio."""
    kwargs = {
        "id": "user-1",
        "name": "Mauri",
        "lastname": "Salinas",
        "email": Email("mauri@mail.com"),
        "password_hash": "hash",
        "birthdate": date(2000, 1, 1),
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=f"{field} cannot be empty"):
        User(**kwargs)


# Tipo de test: Unit
def test_should_raise_when_birthdate_is_in_future() -> None:
    """Valida que lanza cuando fecha de nacimiento es in futuro."""
    future_birthdate = date.today() + timedelta(days=1)

    with pytest.raises(ValueError, match="birthdate cannot be in the future"):
        User(
            id="user-1",
            name="Mauri",
            lastname="Salinas",
            email=Email("mauri@mail.com"),
            password_hash="hash",
            birthdate=future_birthdate,
        )
