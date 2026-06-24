from app.features.auth.infrastructure.managers.password_manager_impl import PasswordManagerImpl


# Tipo de test: Unit
def test_should_hash_and_verify_password() -> None:
    """Valida que hash y verifica contrasena."""
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


# Tipo de test: Unit
def test_should_return_false_for_malformed_hash() -> None:
    """S8: un hash malformado en la BD debe dar fallo de auth limpio (False), no 500."""
    manager = PasswordManagerImpl()

    assert manager.verify_password("any-password", "not-a-valid-argon2-hash") is False
