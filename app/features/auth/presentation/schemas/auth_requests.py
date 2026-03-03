from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request schema used to register a new user account."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    lastname: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    birthdate: date


class RefreshTokenRequest(BaseModel):
    """Request schema used to refresh an access token."""

    refresh_token: str = Field(min_length=1)
