from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    lastname: str = Field(min_length=1, max_length=100)
    email: EmailStr
    birthdate: date


class UpdateUserRequest(UserRequest):
    pass
