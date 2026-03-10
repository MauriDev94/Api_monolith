from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.features.users.domain.value_objects.email import Email


class UserRequest(BaseModel):
    """Base request schema for user create/update payloads."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    lastname: str = Field(min_length=1, max_length=100)
    email: EmailStr
    birthdate: date

    @field_validator("email")
    @classmethod
    def validate_email_policy(cls, value: EmailStr) -> EmailStr:
        """Apply domain email policy at transport boundary."""
        Email(str(value))
        return value


class UpdateUserRequest(UserRequest):
    """Request schema for update user endpoint."""
