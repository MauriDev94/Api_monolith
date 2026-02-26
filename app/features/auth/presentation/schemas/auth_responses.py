from datetime import date, datetime

from pydantic import BaseModel


class AuthUserResponse(BaseModel):
    id: str
    name: str
    lastname: str
    email: str
    birthdate: date
    created_at: datetime | None
    updated_at: datetime | None


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RegisterResponse(BaseModel):
    user: AuthUserResponse


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    tokens: TokenPairResponse


class CurrentUserResponse(BaseModel):
    user: AuthUserResponse
