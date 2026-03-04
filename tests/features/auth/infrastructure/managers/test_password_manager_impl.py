from app.features.auth.infrastructure.managers.password_manager_impl import PasswordManagerImpl


# Tipo de test: Unit
def test_should_hash_and_verify_password() -> None:
    """Valida que hash y verificar contrasena."""
    manager = PasswordManagerImpl()

    hashed_password = manager.hash_password("plain-password")

    assert hashed_password != "plain-password"
    assert manager.verify_password("plain-password", hashed_password) is True


# Tipo de test: Unit
def test_should_return_false_when_password_is_invalid() -> None:
    """Valida que retorna false cuando contrasena es invalido."""
    manager = PasswordManagerImpl()
    hashed_password = manager.hash_password("plain-password")

    assert manager.verify_password("wrong-password", hashed_password) is False
