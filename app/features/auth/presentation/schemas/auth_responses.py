from datetime import date, datetime

from pydantic import BaseModel


class AuthUserResponse(BaseModel):
    """Public user payload returned by auth endpoints."""

    id: str
    name: str
    lastname: str
    email: str
    birthdate: date
    created_at: datetime | None
    updated_at: datetime | None


class TokenPairResponse(BaseModel):
    """Access/refresh token pair exposed in API responses."""

    access_token: str
    refresh_token: str
    token_type: str


class RegisterResponse(BaseModel):
    """Response schema for register endpoint."""

    user: AuthUserResponse


class LoginResponse(BaseModel):
    """Response schema for login endpoint."""

    access_token: str
    token_type: str
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response schema for refresh endpoint."""

    tokens: TokenPairResponse


class CurrentUserResponse(BaseModel):
    """Response schema for current-user endpoint."""

    user: AuthUserResponse
