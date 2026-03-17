from dataclasses import dataclass


@dataclass(slots=True)
class VerifyOtpParams:
    """Input DTO for verifying an OTP."""

    user_id: str
    code: str
    purpose: str
