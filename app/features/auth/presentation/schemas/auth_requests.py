from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.features.users.domain.value_objects.email import Email


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


class RefreshTokenRequest(BaseModel):
    """Request schema used to refresh an access token."""

    refresh_token: str = Field(min_length=1)


class VerifyOtpRequest(BaseModel):
    """Request schema used to verify an OTP."""

    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ChangePasswordRequest(BaseModel):
    """Request schema used to change password with OTP."""

    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)
