from datetime import date, datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Public representation of a user in API responses."""

    id: str
    name: str
    lastname: str
    email: str
    birthdate: date
    created_at: datetime | None
    updated_at: datetime | None


class GetAllUsersResponse(BaseModel):
    """Response schema for users list endpoint."""

    users: list[UserResponse]


class GetUserByIdResponse(BaseModel):
    """Response schema for get user by id endpoint."""

    user: UserResponse


class UpdateUserResponse(BaseModel):
    """Response schema for update user endpoint."""

    user: UserResponse


class DeleteUserResponse(BaseModel):
    """Response schema for delete user endpoint."""

    message: str
