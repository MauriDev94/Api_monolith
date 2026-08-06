from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateTodoRequest(BaseModel):
    """Request schema for creating a todo.

    Solo restricciones de transporte (tipos y tamaño del payload). La regla de
    negocio "no se puede agendar en el pasado" vive en `Todo.create_new()`, para
    que aplique venga la petición de donde venga y no solo por HTTP.
    """

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
