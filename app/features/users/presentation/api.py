from typing import Annotated

from fastapi import Depends

from app.core.exceptions.exceptions import InternalServerErrorException, ResourceNotFoundException
from app.core.router.router import get_versioned_router
from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.users.application.dto.delete_user_params import DeleteUserParams
from app.features.users.application.usecases.delete_user_use_case import DeleteUser
from app.features.users.application.usecases.get_all_users_use_case import GetAllUsers
from app.features.users.application.usecases.get_user_by_id_use_case import GetUserById
from app.features.users.application.usecases.update_user_use_case import UpdateUser
from app.features.users.di.dependencies import (
    get_delete_user_use_case,
    get_get_all_users_use_case,
    get_get_user_by_id_use_case,
    get_update_user_use_case,
)
from app.features.users.domain.entities.user import User
from app.features.users.presentation.mappers.user_mapper import (
    map_update_user_request_to_params,
    map_user_entity_to_response,
    map_user_id_to_params,
)
from app.features.users.presentation.schemas.user_requests import UpdateUserRequest
from app.features.users.presentation.schemas.user_responses import (
    DeleteUserResponse,
    GetAllUsersResponse,
    GetUserByIdResponse,
    UpdateUserResponse,
)

v1_router = get_versioned_router("v1")


def _require_user_id(current_user: User) -> str:
    """Guarantee a non-empty authenticated user id for authorization checks."""
    if current_user.id is None:
        raise InternalServerErrorException("authenticated user id is missing")
    return current_user.id


def _ensure_self_access(path_user_id: str, current_user: User) -> None:
    """Allow access only to the authenticated user's own resource."""
    if path_user_id != _require_user_id(current_user):
        # Keep not-found semantics to avoid user-id enumeration.
        raise ResourceNotFoundException("user not found")


@v1_router.get("/users")
def get_all_users(
    _: Annotated[User, Depends(get_authenticated_user)],
    get_all_users_use_case: Annotated[GetAllUsers, Depends(get_get_all_users_use_case)],
) -> GetAllUsersResponse:
    """List all users for authenticated clients."""
    users = get_all_users_use_case.execute()
    return GetAllUsersResponse(users=[map_user_entity_to_response(user) for user in users])


@v1_router.get("/users/{user_id}")
def get_user_by_id(
    user_id: str,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    get_user_by_id_use_case: Annotated[GetUserById, Depends(get_get_user_by_id_use_case)],
) -> GetUserByIdResponse:
    """Return a single user by identifier."""
    _ensure_self_access(path_user_id=user_id, current_user=current_user)
    params = map_user_id_to_params(user_id)
    user = get_user_by_id_use_case.execute(params)
    return GetUserByIdResponse(user=map_user_entity_to_response(user))


@v1_router.put("/users/{user_id}")
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    update_user_use_case: Annotated[UpdateUser, Depends(get_update_user_use_case)],
) -> UpdateUserResponse:
    """Update user profile data."""
    _ensure_self_access(path_user_id=user_id, current_user=current_user)
    params = map_update_user_request_to_params(user_id, request)
    user = update_user_use_case.execute(params)
    return UpdateUserResponse(user=map_user_entity_to_response(user))


@v1_router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_authenticated_user)],
    delete_user_use_case: Annotated[DeleteUser, Depends(get_delete_user_use_case)],
) -> DeleteUserResponse:
    """Delete an existing user."""
    _ensure_self_access(path_user_id=user_id, current_user=current_user)
    delete_user_use_case.execute(DeleteUserParams(user_id=user_id))
    return DeleteUserResponse(message="User deleted successfully")
