from dataclasses import dataclass


@dataclass(slots=True)
class GetUserByIdParams:
    """Input DTO for retrieving a user by id."""

    user_id: str
