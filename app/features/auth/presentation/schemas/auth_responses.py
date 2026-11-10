from datetime import date, datetime

from pydantic import BaseModel


class AuthUserResponse(BaseModel):
    """Public user payload returned by auth endpoints."""

    id: str
    name: str
    lastname: str
    email: str
    birthdate: date | None
    created_at: datetime | None
    updated_at: datetime | None


class TokenPairResponse(BaseModel):
    """Access token exposed in API responses (the refresh token travels only in the cookie)."""

    access_token: str
    token_type: str


class RegisterResponse(BaseModel):
    """Response schema for register endpoint."""

    user: AuthUserResponse


class LoginResponse(BaseModel):
    """Response schema for login endpoint."""

    access_token: str
    token_type: str


class RefreshTokenResponse(BaseModel):
    """Response schema for refresh endpoint."""

    tokens: TokenPairResponse


class CurrentUserResponse(BaseModel):
    """Response schema for current-user endpoint."""

    user: AuthUserResponse


class OtpResponse(BaseModel):
    """Response schema for OTP endpoints."""

    message: str
