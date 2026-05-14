from enum import StrEnum


class OtpPurpose(StrEnum):
    """Valid OTP purposes supported by the auth domain."""

    PASSWORD_CHANGE = "password_change"
