from datetime import date, datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Public representation of a user in API responses."""

    id: str
    name: str
    lastname: str
    email: str
    birthdate: date | None
    created_at: datetime | None
    updated_at: datetime | None


class GetUserByIdResponse(BaseModel):
    """Response schema for get user by id endpoint."""

    user: UserResponse


class UpdateUserResponse(BaseModel):
    """Response schema for update user endpoint."""

    user: UserResponse
