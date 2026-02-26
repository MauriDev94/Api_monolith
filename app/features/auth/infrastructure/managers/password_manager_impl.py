from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.features.auth.application.contracts.password_manager import PasswordManager


class PasswordManagerImpl(PasswordManager):
    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def hash_password(self, raw_password: str) -> str:
        return self._hasher.hash(raw_password)

    def verify_password(self, raw_password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, raw_password)
        except VerifyMismatchError:
            return False
