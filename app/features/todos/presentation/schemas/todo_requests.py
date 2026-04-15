from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateTodoRequest(BaseModel):
    """Request schema for creating a todo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    due_date: datetime | None = Field(default=None)


class UpdateTodoRequest(BaseModel):
    """Request schema for updating a todo."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    is_completed: bool
    due_date: datetime | None = Field(default=None)
