from datetime import datetime

from pydantic import BaseModel


class TodoResponse(BaseModel):
    """Public representation of a todo in API responses."""

    id: str
    user_id: str
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime | None
    updated_at: datetime | None


class CreateTodoResponse(BaseModel):
    """Response schema for create todo endpoint."""

    todo: TodoResponse


class GetTodosResponse(BaseModel):
    """Response schema for list todos endpoint."""

    todos: list[TodoResponse]


class GetTodoByIdResponse(BaseModel):
    """Response schema for get todo by id endpoint."""

    todo: TodoResponse


class UpdateTodoResponse(BaseModel):
    """Response schema for update todo endpoint."""

    todo: TodoResponse


class DeleteTodoResponse(BaseModel):
    """Response schema for delete todo endpoint."""

    message: str
