import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Email:
    """Value object that encapsulates normalization and email invariants."""

    value: str

    _MAX_EMAIL_LENGTH = 254
    _MAX_LOCAL_PART_LENGTH = 64
    # Local-part (antes de @): solo letras, números y estos caracteres: . _ -
    # Ejemplos válidos: user.name, foo_bar, admin-1
    _LOCAL_PART_PATTERN = re.compile(r"^[a-z0-9._-]+$")
    # Cada etiqueta del dominio (separada por '.'): solo letras.
    # Ejemplos válidos: gmail, hotmail, outlook
    _DOMAIN_LABEL_PATTERN = re.compile(r"^[a-z]+$")

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        self._validate(normalized)
        object.__setattr__(self, "value", normalized)

    def _validate(self, email: str) -> None:
        if not email or len(email) > self._MAX_EMAIL_LENGTH:
            raise ValueError("invalid email format")

        if email.count("@") != 1:
            raise ValueError("invalid email format")

        local_part, domain_part = email.split("@")
        if not local_part or not domain_part:
            raise ValueError("invalid email format")

        if len(local_part) > self._MAX_LOCAL_PART_LENGTH:
            raise ValueError("invalid email format")

        if local_part.startswith(".") or local_part.endswith(".") or ".." in local_part:
            raise ValueError("invalid email format")

        if not self._LOCAL_PART_PATTERN.fullmatch(local_part):
            raise ValueError("invalid email format")

        if domain_part.startswith(".") or domain_part.endswith(".") or ".." in domain_part:
            raise ValueError("invalid email format")

        labels = domain_part.split(".")
        if len(labels) < 2:
            raise ValueError("invalid email format")

        if any(not self._DOMAIN_LABEL_PATTERN.fullmatch(label) for label in labels):
            raise ValueError("invalid email format")

        if len(labels[-1]) < 2:
            raise ValueError("invalid email format")

    def __str__(self) -> str:
        return self.value
