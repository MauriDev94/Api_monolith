from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _reject_past_due_date(value: datetime | None) -> datetime | None:
    """Regla de creación: el due_date provisto por el usuario no puede ser pasado."""
    if value is not None:
        aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        if aware < datetime.now(UTC):
            raise ValueError("due_date cannot be in the past")
    return value


class CreateTodoRequest(BaseModel):
    """Request schema for creating a todo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    due_date: datetime | None = Field(default=None)

    @field_validator("due_date")
    @classmethod
    def validate_due_date_not_past(cls, value: datetime | None) -> datetime | None:
        return _reject_past_due_date(value)


class UpdateTodoRequest(BaseModel):
    """Request schema for updating a todo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    is_completed: bool
    due_date: datetime | None = Field(default=None)
