from datetime import date, timedelta

import pytest

from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


# Tipo de test: Unit
def test_should_normalize_user_text_fields_and_email() -> None:
    """Valida que normaliza nombre, apellido, email y hash en la construccion."""
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
    """Valida que lanza error cuando un campo de texto requerido esta vacio."""
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
    """Valida que lanza error cuando la fecha de nacimiento esta en el futuro."""
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


# Tipo de test: Unit
def test_should_mutate_user_with_behavior_methods() -> None:
    """Valida que los metodos de dominio mutan estado de usuario con normalizacion."""
    user = User(
        id="user-1",
        name="Mauri",
        lastname="Salinas",
        email=Email("mauri@mail.com"),
        password_hash="hash",
        birthdate=date(2000, 1, 1),
    )

    user.change_name("  Mauricio ")
    user.change_lastname(" Salas ")
    user.change_email(" MAURICIO@mail.com ")
    user.change_birthdate(date(1999, 1, 1))

    assert user.name == "Mauricio"
    assert user.lastname == "Salas"
    assert user.email.value == "mauricio@mail.com"
    assert user.birthdate == date(1999, 1, 1)
    assert user.updated_at is not None


# Tipo de test: Unit
def test_should_raise_when_changing_user_to_invalid_values() -> None:
    """Valida que los metodos de dominio mantienen invariantes de usuario."""
    user = User(
        id="user-1",
        name="Mauri",
        lastname="Salinas",
        email=Email("mauri@mail.com"),
        password_hash="hash",
        birthdate=date(2000, 1, 1),
    )

    with pytest.raises(ValueError, match="name cannot be empty"):
        user.change_name("   ")

    with pytest.raises(ValueError, match="birthdate cannot be in the future"):
        user.change_birthdate(date.today() + timedelta(days=1))
