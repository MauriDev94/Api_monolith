from dataclasses import dataclass


@dataclass(slots=True)
class RequestOtpParams:
    """Input DTO for requesting an OTP."""

    user_id: str
    purpose: str
