from abc import ABC, abstractmethod


class PasswordManager(ABC):
    """Application port for password hashing and verification."""

    @abstractmethod
    def hash_password(self, raw_password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, raw_password: str, password_hash: str) -> bool:
        pass
