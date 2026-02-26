from dataclasses import dataclass


@dataclass(slots=True)
class DeleteUserParams:
    """Input DTO for deleting a user by id."""

    user_id: str
