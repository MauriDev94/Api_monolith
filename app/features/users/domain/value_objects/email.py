from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Email:
    """Value object that encapsulates normalization and email invariants."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email format")

        local_part, domain_part = normalized.split("@")
        if not local_part or not domain_part or "." not in domain_part:
            raise ValueError("invalid email format")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
