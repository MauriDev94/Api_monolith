from app.features.users.application.dto.get_user_by_id_params import GetUserByIdParams
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.domain.entities.user import User
from app.features.users.presentation.schemas.user_requests import UpdateUserRequest
from app.features.users.presentation.schemas.user_responses import UserResponse


def map_update_user_request_to_params(user_id: str, request: UpdateUserRequest) -> UpdateUserParams:
    return UpdateUserParams(
        id=user_id,
        name=request.name,
        lastname=request.lastname,
        email=str(request.email),
        birthdate=request.birthdate,
    )


def map_user_id_to_params(user_id: str) -> GetUserByIdParams:
    return GetUserByIdParams(user_id=user_id)


def map_user_entity_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id or "",
        name=user.name,
        lastname=user.lastname,
        email=user.email.value,
        birthdate=user.birthdate,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
