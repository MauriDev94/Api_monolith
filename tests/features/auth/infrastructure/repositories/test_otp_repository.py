import hashlib
import hmac
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.features.auth.domain.entities.otp_code import OtpCode
from app.features.auth.domain.value_objects.otp_purpose import OtpPurpose
from app.features.auth.infrastructure.models.otp_model import OtpModel
from app.features.auth.infrastructure.repositories.otp_repository import OtpRepository
from app.features.users.infrastructure.repositories.user_provider_repository import (
    UserProviderRepository,
)

_TEST_SECRET = "test-secret-key"


def _seed_user_id(session: Session) -> str:
    provider = UserProviderRepository(session=session)
    user = provider.create_user(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        password_hash="hashed-password",
        birthdate=date(2000, 1, 1),
    )
    return user.id or ""


# Tipo de test: Integration
def test_should_create_and_return_persisted_otp(db_session: Session) -> None:
    repository = OtpRepository(session=db_session, secret_key=_TEST_SECRET)
    user_id = _seed_user_id(db_session)
    otp = OtpCode.create(user_id=user_id, purpose=OtpPurpose.PASSWORD_CHANGE)

    persisted = repository.save(otp)

    assert persisted.id is not None
    assert persisted.user_id == user_id
    assert persisted.purpose == OtpPurpose.PASSWORD_CHANGE
    assert persisted.code == otp.code
    persisted_model = db_session.query(OtpModel).filter(OtpModel.id == persisted.id).first()
    assert persisted_model is not None
    expected_hash = hmac.new(
        _TEST_SECRET.encode("utf-8"), otp.code.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert persisted_model.code_hash == expected_hash


# Tipo de test: Integration
def test_should_find_valid_otp_when_exists(db_session: Session) -> None:
    repository = OtpRepository(session=db_session, secret_key=_TEST_SECRET)
    user_id = _seed_user_id(db_session)
    persisted = repository.save(OtpCode.create(user_id=user_id, purpose=OtpPurpose.PASSWORD_CHANGE))

    found = repository.find_valid(
        user_id=user_id, code=persisted.code, purpose=OtpPurpose.PASSWORD_CHANGE
    )

    assert found is not None
    assert found.id == persisted.id


# Tipo de test: Integration
def test_should_not_find_otp_when_expired(db_session: Session) -> None:
    repository = OtpRepository(session=db_session, secret_key=_TEST_SECRET)
    user_id = _seed_user_id(db_session)
    expired = OtpCode(
        id=None,
        user_id=user_id,
        code="123456",
        purpose=OtpPurpose.PASSWORD_CHANGE,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
        created_at=datetime.now(UTC) - timedelta(minutes=2),
    )
    persisted = repository.save(expired)

    found = repository.find_valid(
        user_id=user_id, code=persisted.code, purpose=OtpPurpose.PASSWORD_CHANGE
    )

    assert found is None


# Tipo de test: Integration
def test_should_invalidate_all_pending_otps_for_user_and_purpose(db_session: Session) -> None:
    repository = OtpRepository(session=db_session, secret_key=_TEST_SECRET)
    user_id = _seed_user_id(db_session)
    first = repository.save(OtpCode.create(user_id=user_id, purpose=OtpPurpose.PASSWORD_CHANGE))
    second = repository.save(OtpCode.create(user_id=user_id, purpose=OtpPurpose.PASSWORD_CHANGE))

    repository.invalidate_all(user_id=user_id, purpose=OtpPurpose.PASSWORD_CHANGE)

    assert (
        repository.find_valid(user_id=user_id, code=first.code, purpose=OtpPurpose.PASSWORD_CHANGE)
        is None
    )
    assert (
        repository.find_valid(user_id=user_id, code=second.code, purpose=OtpPurpose.PASSWORD_CHANGE)
        is None
    )


# Tipo de test: Integration
def test_should_update_used_otp_state(db_session: Session) -> None:
    repository = OtpRepository(session=db_session, secret_key=_TEST_SECRET)
    user_id = _seed_user_id(db_session)
    persisted = repository.save(OtpCode.create(user_id=user_id, purpose=OtpPurpose.PASSWORD_CHANGE))

    persisted.consume()
    repository.save(persisted)

    assert (
        repository.find_valid(
            user_id=user_id, code=persisted.code, purpose=OtpPurpose.PASSWORD_CHANGE
        )
        is None
    )
