from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.auth.infrastructure.repositories.token_revocation_repository import (
    TokenRevocationRepository,
)


def _seed_user(session: Session, email: str = "mauri@mail.com") -> str:
    """Crea un usuario real: auth_refresh_tokens.user_id tiene FK a users.id en Postgres."""
    auth_repository = AuthRepository(session=session)
    user = auth_repository.register_user(
        params=RegisterUserParams(
            name="Mauri",
            lastname="Salinas",
            email=email,
            password="plain1234",
            birthdate=date(2000, 1, 1),
        ),
        password_hash="hashed-password",
    )
    return user.id or ""


def test_should_store_active_token(db_session: Session) -> None:
    repository = TokenRevocationRepository(session=db_session)
    user_id = _seed_user(db_session)
    jti = "test-jti-123"
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    repository.store_active(jti=jti, user_id=user_id, expires_at=expires_at)

    is_revoked = repository.is_revoked(jti=jti)
    assert is_revoked is False


def test_should_revoke_token(db_session: Session) -> None:
    repository = TokenRevocationRepository(session=db_session)
    user_id = _seed_user(db_session)
    jti = "test-jti-123"
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    repository.store_active(jti=jti, user_id=user_id, expires_at=expires_at)
    repository.revoke(jti=jti)

    is_revoked = repository.is_revoked(jti=jti)
    assert is_revoked is True


def test_should_return_revoked_for_nonexistent_jti(db_session: Session) -> None:
    repository = TokenRevocationRepository(session=db_session)

    is_revoked = repository.is_revoked(jti="nonexistent-jti")

    assert is_revoked is True


def test_should_return_revoked_for_expired_token(db_session: Session) -> None:
    repository = TokenRevocationRepository(session=db_session)
    user_id = _seed_user(db_session)
    jti = "test-jti-123"
    expires_at = datetime.now(UTC) - timedelta(minutes=1)  # Expired

    repository.store_active(jti=jti, user_id=user_id, expires_at=expires_at)

    is_revoked = repository.is_revoked(jti=jti)
    assert is_revoked is True


def test_should_revoke_all_tokens_for_user(db_session: Session) -> None:
    repository = TokenRevocationRepository(session=db_session)
    user_id = _seed_user(db_session)

    # Store multiple tokens
    for i in range(3):
        repository.store_active(
            jti=f"jti-{i}",
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    # Revoke all
    repository.revoke_all_for_user(user_id=user_id)

    # All should be revoked
    for i in range(3):
        is_revoked = repository.is_revoked(jti=f"jti-{i}")
        assert is_revoked is True


def test_should_not_revoke_tokens_for_other_users(db_session: Session) -> None:
    repository = TokenRevocationRepository(session=db_session)
    user_a = _seed_user(db_session, email="user-a@mail.com")
    user_b = _seed_user(db_session, email="user-b@mail.com")

    repository.store_active(
        jti="jti-a", user_id=user_a, expires_at=datetime.now(UTC) + timedelta(hours=1)
    )
    repository.store_active(
        jti="jti-b", user_id=user_b, expires_at=datetime.now(UTC) + timedelta(hours=1)
    )

    # Revoke all for user_a only
    repository.revoke_all_for_user(user_id=user_a)

    assert repository.is_revoked(jti="jti-a") is True
    assert repository.is_revoked(jti="jti-b") is False
