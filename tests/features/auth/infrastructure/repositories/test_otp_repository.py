from datetime import date, datetime, timedelta, timezone
import hashlib

from sqlalchemy.orm import Session

from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.auth.infrastructure.repositories.otp_repository import OtpRepository
from app.features.auth.domain.entities.otp_code import OtpCode
from app.features.auth.infrastructure.models.otp_model import OtpModel


def _seed_user_id(session: Session) -> str:
    auth_repository = AuthRepository(session=session)
    user = auth_repository.register_user(
        params=RegisterUserParams(
            name="Mauri",
            lastname="Salinas",
            email="mauri@mail.com",
            password="plain1234",
            birthdate=date(2000, 1, 1),
        ),
        password_hash="hashed-password",
    )
    return user.id or ""


# Tipo de test: Integration
def test_should_create_and_return_persisted_otp(db_session: Session) -> None:
    repository = OtpRepository(session=db_session)
    user_id = _seed_user_id(db_session)
    otp = OtpCode.create(user_id=user_id, purpose="login")

    persisted = repository.save(otp)

    assert persisted.id is not None
    assert persisted.user_id == user_id
    assert persisted.purpose == "login"
    assert persisted.code == otp.code
    persisted_model = db_session.query(OtpModel).filter(OtpModel.id == persisted.id).first()
    assert persisted_model is not None
    assert persisted_model.code_hash == hashlib.sha256(otp.code.encode("utf-8")).hexdigest()


# Tipo de test: Integration
def test_should_find_valid_otp_when_exists(db_session: Session) -> None:
    repository = OtpRepository(session=db_session)
    user_id = _seed_user_id(db_session)
    persisted = repository.save(OtpCode.create(user_id=user_id, purpose="login"))

    found = repository.find_valid(user_id=user_id, code=persisted.code, purpose="login")

    assert found is not None
    assert found.id == persisted.id


# Tipo de test: Integration
def test_should_not_find_otp_when_expired(db_session: Session) -> None:
    repository = OtpRepository(session=db_session)
    user_id = _seed_user_id(db_session)
    expired = OtpCode(
        id=None,
        user_id=user_id,
        code="123456",
        purpose="login",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=2),
    )
    persisted = repository.save(expired)

    found = repository.find_valid(user_id=user_id, code=persisted.code, purpose="login")

    assert found is None


# Tipo de test: Integration
def test_should_invalidate_all_pending_otps_for_user_and_purpose(db_session: Session) -> None:
    repository = OtpRepository(session=db_session)
    user_id = _seed_user_id(db_session)
    first = repository.save(OtpCode.create(user_id=user_id, purpose="login"))
    second = repository.save(OtpCode.create(user_id=user_id, purpose="login"))

    repository.invalidate_all(user_id=user_id, purpose="login")

    assert repository.find_valid(user_id=user_id, code=first.code, purpose="login") is None
    assert repository.find_valid(user_id=user_id, code=second.code, purpose="login") is None


# Tipo de test: Integration
def test_should_update_used_otp_state(db_session: Session) -> None:
    repository = OtpRepository(session=db_session)
    user_id = _seed_user_id(db_session)
    persisted = repository.save(OtpCode.create(user_id=user_id, purpose="login"))

    persisted.consume()
    repository.save(persisted)

    assert repository.find_valid(user_id=user_id, code=persisted.code, purpose="login") is None
