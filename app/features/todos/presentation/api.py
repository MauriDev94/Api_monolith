from typing import Annotated

from fastapi import Depends, status

from app.core.exceptions.exceptions import InternalServerErrorException
from app.core.router.router import get_versioned_router
from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.todos.application.usecases.create_todo_use_case import CreateTodo
from app.features.todos.application.usecases.delete_todo_use_case import DeleteTodo
from app.features.todos.application.usecases.get_todo_by_id_use_case import GetTodoById
from app.features.todos.application.usecases.get_todos_use_case import GetTodos
from app.features.todos.application.usecases.update_todo_use_case import UpdateTodo
from app.features.todos.di.dependencies import (
    get_create_todo_use_case,
    get_delete_todo_use_case,
    get_get_todo_by_id_use_case,
    get_get_todos_use_case,
    get_update_todo_use_case,
)
from app.features.todos.presentation.mappers.todo_mapper import (
    map_create_todo_request_to_params,
    map_todo_entity_to_response,
    map_todo_id_to_delete_params,
    map_todo_id_to_get_params,
    map_update_todo_request_to_params,
    map_user_id_to_get_todos_params,
)
from app.features.todos.presentation.schemas.todo_requests import CreateTodoRequest, UpdateTodoRequest
from app.features.todos.presentation.schemas.todo_responses import (
    CreateTodoResponse,
    DeleteTodoResponse,
    GetTodoByIdResponse,
    GetTodosResponse,
    UpdateTodoResponse,
)
from app.features.users.domain.entities.user import User

v1_router = get_versioned_router("v1")


def _require_user_id(current_user: User) -> str:
    """Guarantee a non-empty authenticated user id for ownership checks."""
    if current_user.id is None:
        raise InternalServerErrorException("authenticated user id is missing")
    return current_user.id


@v1_router.post("/todos", response_model=CreateTodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    request: CreateTodoRequest,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    create_todo_use_case: Annotated[CreateTodo, Depends(get_create_todo_use_case)],
) -> CreateTodoResponse:
    """Create a todo for the authenticated user."""
    params = map_create_todo_request_to_params(_require_user_id(current_user), request)
    todo = create_todo_use_case.execute(params)
    return CreateTodoResponse(todo=map_todo_entity_to_response(todo))


@v1_router.get("/todos", response_model=GetTodosResponse)
def get_todos(
    current_user: Annotated[User, Depends(get_authenticated_user)],
    get_todos_use_case: Annotated[GetTodos, Depends(get_get_todos_use_case)],
) -> GetTodosResponse:
    """List todos owned by the authenticated user."""
    params = map_user_id_to_get_todos_params(_require_user_id(current_user))
    todos = get_todos_use_case.execute(params)
    return GetTodosResponse(todos=[map_todo_entity_to_response(todo) for todo in todos])


@v1_router.get("/todos/{todo_id}", response_model=GetTodoByIdResponse)
def get_todo_by_id(
    todo_id: str,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    get_todo_by_id_use_case: Annotated[GetTodoById, Depends(get_get_todo_by_id_use_case)],
) -> GetTodoByIdResponse:
    """Return one todo by identifier if it belongs to the current user."""
    params = map_todo_id_to_get_params(todo_id, _require_user_id(current_user))
    todo = get_todo_by_id_use_case.execute(params)
    return GetTodoByIdResponse(todo=map_todo_entity_to_response(todo))


@v1_router.put("/todos/{todo_id}", response_model=UpdateTodoResponse)
def update_todo(
    todo_id: str,
    request: UpdateTodoRequest,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    update_todo_use_case: Annotated[UpdateTodo, Depends(get_update_todo_use_case)],
) -> UpdateTodoResponse:
    """Update one todo owned by the authenticated user."""
    params = map_update_todo_request_to_params(todo_id, _require_user_id(current_user), request)
    todo = update_todo_use_case.execute(params)
    return UpdateTodoResponse(todo=map_todo_entity_to_response(todo))


@v1_router.delete("/todos/{todo_id}", response_model=DeleteTodoResponse)
def delete_todo(
    todo_id: str,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    delete_todo_use_case: Annotated[DeleteTodo, Depends(get_delete_todo_use_case)],
) -> DeleteTodoResponse:
    """Delete one todo owned by the authenticated user."""
    params = map_todo_id_to_delete_params(todo_id, _require_user_id(current_user))
    delete_todo_use_case.execute(params)
    return DeleteTodoResponse(message="Todo deleted successfully")
