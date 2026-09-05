import re
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.features.users.domain.value_objects.email import Email


def _validate_password_complexity(password: str) -> str:
    """Validate password meets complexity requirements: 8+ chars, letters + numbers."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[a-zA-Z]", password):
        raise ValueError("Password must contain letters")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain numbers")
    return password


class RegisterRequest(BaseModel):
    """Request schema used to register a new user account."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    lastname: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    birthdate: date

    @field_validator("email")
    @classmethod
    def validate_email_policy(cls, value: EmailStr) -> EmailStr:
        """Apply domain email policy at transport boundary."""
        Email(str(value))
        return value

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        """Validate password meets complexity requirements."""
        return _validate_password_complexity(value)


class RefreshTokenRequest(BaseModel):
    """Request schema used to refresh an access token."""

    refresh_token: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    """Request schema used to change password with OTP."""

    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        """Validate password meets complexity requirements."""
        return _validate_password_complexity(value)
