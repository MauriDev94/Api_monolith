from dataclasses import dataclass


@dataclass(slots=True)
class ChangePasswordWithOtpParams:
    """Input DTO for changing password using OTP validation."""

    user_id: str
    code: str
    new_password: str
