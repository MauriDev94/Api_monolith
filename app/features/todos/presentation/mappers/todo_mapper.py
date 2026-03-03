from app.features.todos.application.dto.create_todo_params import CreateTodoParams
from app.features.todos.application.dto.delete_todo_params import DeleteTodoParams
from app.features.todos.application.dto.get_todo_by_id_params import GetTodoByIdParams
from app.features.todos.application.dto.get_todos_params import GetTodosParams
from app.features.todos.application.dto.update_todo_params import UpdateTodoParams
from app.features.todos.domain.entities.todo import Todo
from app.features.todos.presentation.schemas.todo_requests import CreateTodoRequest, UpdateTodoRequest
from app.features.todos.presentation.schemas.todo_responses import TodoResponse


def map_create_todo_request_to_params(user_id: str, request: CreateTodoRequest) -> CreateTodoParams:
    """Map create request payload to use-case parameters."""
    return CreateTodoParams(
        user_id=user_id,
        title=request.title,
        description=request.description,
    )


def map_update_todo_request_to_params(todo_id: str, user_id: str, request: UpdateTodoRequest) -> UpdateTodoParams:
    """Map update request payload and path params to use-case parameters."""
    return UpdateTodoParams(
        todo_id=todo_id,
        user_id=user_id,
        title=request.title,
        description=request.description,
        is_completed=request.is_completed,
    )


def map_todo_id_to_get_params(todo_id: str, user_id: str) -> GetTodoByIdParams:
    """Map path params to get-by-id DTO."""
    return GetTodoByIdParams(todo_id=todo_id, user_id=user_id)


def map_user_id_to_get_todos_params(user_id: str) -> GetTodosParams:
    """Map authenticated user id to list DTO."""
    return GetTodosParams(user_id=user_id)


def map_todo_id_to_delete_params(todo_id: str, user_id: str) -> DeleteTodoParams:
    """Map path params to delete DTO."""
    return DeleteTodoParams(todo_id=todo_id, user_id=user_id)


def map_todo_entity_to_response(todo: Todo) -> TodoResponse:
    """Map todo domain entity to HTTP response schema."""
    return TodoResponse(
        id=todo.id or "",
        user_id=todo.user_id,
        title=todo.title,
        description=todo.description,
        is_completed=todo.is_completed,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
    )
