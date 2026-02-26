from datetime import date, datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    name: str
    lastname: str
    email: str
    birthdate: date
    created_at: datetime | None
    updated_at: datetime | None


class GetAllUsersResponse(BaseModel):
    users: list[UserResponse]


class GetUserByIdResponse(BaseModel):
    user: UserResponse


class UpdateUserResponse(BaseModel):
    user: UserResponse


class DeleteUserResponse(BaseModel):
    message: str
