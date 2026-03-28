from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import DatabaseError
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.infrastructure.models.refresh_token_model import RefreshTokenModel


class TokenRevocationRepository(TokenRevocationStore):
    """SQLAlchemy-backed refresh token revocation store."""

    def __init__(self, session: Session):
        self.session = session

    def store_active(self, jti: str, user_id: str, expires_at: datetime) -> None:
        try:
            model = RefreshTokenModel(
                jti=jti,
                user_id=user_id,
                expires_at=expires_at,
                revoked_at=None,
            )
            self.session.add(model)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to store refresh token") from exc

    def revoke(self, jti: str) -> None:
        try:
            model = (
                self.session.query(RefreshTokenModel)
                .filter(RefreshTokenModel.jti == jti)
                .first()
            )
            if model is None:
                return None
            model.revoked_at = datetime.now(timezone.utc)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to revoke refresh token") from exc

    def is_revoked(self, jti: str) -> bool:
        try:
            model = (
                self.session.query(RefreshTokenModel)
                .filter(RefreshTokenModel.jti == jti)
                .first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to check refresh token revocation") from exc

        if model is None:
            return True

        if model.revoked_at is not None:
            return True

        expires_at = model.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return expires_at <= now

    def revoke_all_for_user(self, user_id: str) -> None:
        try:
            now = datetime.now(timezone.utc)
            self.session.query(RefreshTokenModel).filter(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            ).update(
                {RefreshTokenModel.revoked_at: now},
                synchronize_session=False,
            )
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to revoke refresh tokens for user") from exc
