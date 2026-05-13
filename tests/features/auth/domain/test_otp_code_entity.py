from datetime import UTC, datetime, timedelta

import pytest

from app.features.auth.domain.entities.otp_code import OtpCode
from app.features.auth.domain.value_objects.otp_purpose import OtpPurpose


def test_should_create_valid_otp_code() -> None:
    otp = OtpCode.create(user_id="user-1", purpose=OtpPurpose.PASSWORD_CHANGE)

    assert otp.user_id == "user-1"
    assert otp.purpose == OtpPurpose.PASSWORD_CHANGE
    assert len(otp.code) == 6
    assert otp.code.isdigit()
    assert otp.is_valid() is True


@pytest.mark.parametrize(
    "code",
    ["", "12345", "1234567", "abcdef", "12 345", "12-3456"],
    ids=["empty", "short", "long", "alpha", "space", "dash"],
)
def test_should_raise_when_code_is_invalid(code: str) -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="otp code must be exactly 6 digits"):
        OtpCode(
            id=None,
            user_id="user-1",
            code=code,
            purpose=OtpPurpose.PASSWORD_CHANGE,
            expires_at=now + timedelta(minutes=5),
            created_at=now,
        )


def test_should_raise_when_user_id_is_missing() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="otp must be bound to a user"):
        OtpCode(
            id=None,
            user_id="",
            code="123456",
            purpose=OtpPurpose.PASSWORD_CHANGE,
            expires_at=now + timedelta(minutes=5),
            created_at=now,
        )


def test_should_raise_when_purpose_is_missing() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="otp must have a purpose"):
        OtpCode(
            id=None,
            user_id="user-1",
            code="123456",
            purpose="",
            expires_at=now + timedelta(minutes=5),
            created_at=now,
        )


def test_should_raise_when_purpose_is_not_supported() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="invalid otp purpose"):
        OtpCode(
            id=None,
            user_id="user-1",
            code="123456",
            purpose="login",
            expires_at=now + timedelta(minutes=5),
            created_at=now,
        )


def test_should_raise_when_expires_at_is_naive() -> None:
    now = datetime.now()
    with pytest.raises(ValueError, match="expires_at must be timezone-aware"):
        OtpCode(
            id=None,
            user_id="user-1",
            code="123456",
            purpose=OtpPurpose.PASSWORD_CHANGE,
            expires_at=now + timedelta(minutes=5),
            created_at=datetime.now(UTC),
        )


def test_should_be_invalid_when_expired() -> None:
    now = datetime.now(UTC)
    otp = OtpCode(
        id=None,
        user_id="user-1",
        code="123456",
        purpose=OtpPurpose.PASSWORD_CHANGE,
        expires_at=now - timedelta(minutes=1),
        created_at=now - timedelta(minutes=2),
    )

    assert otp.is_expired() is True
    assert otp.is_valid() is False


def test_should_be_invalid_when_used() -> None:
    now = datetime.now(UTC)
    otp = OtpCode(
        id=None,
        user_id="user-1",
        code="123456",
        purpose=OtpPurpose.PASSWORD_CHANGE,
        expires_at=now + timedelta(minutes=5),
        used_at=now,
        created_at=now - timedelta(minutes=1),
    )

    assert otp.is_used() is True
    assert otp.is_valid() is False


def test_should_consume_valid_otp() -> None:
    now = datetime.now(UTC)
    otp = OtpCode(
        id=None,
        user_id="user-1",
        code="123456",
        purpose=OtpPurpose.PASSWORD_CHANGE,
        expires_at=now + timedelta(minutes=5),
        created_at=now,
    )

    otp.consume()

    assert otp.used_at is not None
    assert otp.is_used() is True


def test_should_raise_when_consuming_used_otp() -> None:
    now = datetime.now(UTC)
    otp = OtpCode(
        id=None,
        user_id="user-1",
        code="123456",
        purpose=OtpPurpose.PASSWORD_CHANGE,
        expires_at=now + timedelta(minutes=5),
        used_at=now,
        created_at=now - timedelta(minutes=1),
    )

    with pytest.raises(ValueError, match="otp has already been used"):
        otp.consume()


def test_should_raise_when_consuming_expired_otp() -> None:
    now = datetime.now(UTC)
    otp = OtpCode(
        id=None,
        user_id="user-1",
        code="123456",
        purpose=OtpPurpose.PASSWORD_CHANGE,
        expires_at=now - timedelta(minutes=1),
        created_at=now - timedelta(minutes=2),
    )

    with pytest.raises(ValueError, match="otp has expired"):
        otp.consume()
