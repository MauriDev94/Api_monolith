import hashlib
import hmac
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import DatabaseError
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.domain.entities.otp_code import OtpCode
from app.features.auth.infrastructure.models.otp_model import OtpModel


class OtpRepository(OtpDatasource):
    """SQLAlchemy implementation for OTP persistence operations."""

    def __init__(self, session: Session, secret_key: str):
        self.session = session
        self._secret_key = secret_key

    def save(self, otp: OtpCode) -> OtpCode:
        if otp.id is None:
            return self._create(otp)
        return self._update(otp)

    def _create(self, otp: OtpCode) -> OtpCode:
        model = OtpModel(
            id=str(uuid4()),
            user_id=otp.user_id,
            code_hash=self._hash_code(otp.code),
            purpose=otp.purpose,
            expires_at=otp.expires_at,
            used_at=otp.used_at,
            created_at=otp.created_at or datetime.now(UTC),
        )
        try:
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to store otp") from exc

        return self._to_entity(model, code_override=otp.code)

    def _update(self, otp: OtpCode) -> OtpCode:
        try:
            model = self.session.query(OtpModel).filter(OtpModel.id == otp.id).first()
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to load otp for update") from exc

        if model is None:
            raise DatabaseError("otp not found for update")

        model.code_hash = self._hash_code(otp.code)
        model.purpose = otp.purpose
        model.expires_at = otp.expires_at
        model.used_at = otp.used_at

        try:
            self.session.commit()
            self.session.refresh(model)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to update otp") from exc

        return self._to_entity(model, code_override=otp.code)

    def find_valid(self, user_id: str, code: str, purpose: str) -> OtpCode | None:
        now = datetime.now(UTC)
        code_hash = self._hash_code(code)
        try:
            model = (
                self.session.query(OtpModel)
                .filter(
                    OtpModel.user_id == user_id,
                    OtpModel.code_hash == code_hash,
                    OtpModel.purpose == purpose,
                    OtpModel.used_at.is_(None),
                    OtpModel.expires_at > now,
                )
                .first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to lookup otp") from exc

        if model is None:
            return None
        return self._to_entity(model, code_override=code)

    def invalidate_all(self, user_id: str, purpose: str) -> None:
        now = datetime.now(UTC)
        try:
            self.session.query(OtpModel).filter(
                OtpModel.user_id == user_id,
                OtpModel.purpose == purpose,
                OtpModel.used_at.is_(None),
            ).update(
                {OtpModel.used_at: now},
                synchronize_session=False,
            )
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to invalidate otps") from exc

    @staticmethod
    def _to_entity(model: OtpModel, code_override: str | None = None) -> OtpCode:
        expires_at = OtpRepository._ensure_aware(model.expires_at)
        if expires_at is None:
            raise ValueError(
                f"OTP record {model.id!r} has no expires_at — data integrity violation"
            )
        return OtpCode(
            id=model.id,
            user_id=model.user_id,
            code=code_override or "000000",
            purpose=model.purpose,
            expires_at=expires_at,
            used_at=OtpRepository._ensure_aware(model.used_at),
            created_at=OtpRepository._ensure_aware(model.created_at),
        )

    @staticmethod
    def _ensure_aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    def _hash_code(self, code: str) -> str:
        """HMAC-SHA256 keyeado por un secreto de servidor.

        Sin el secreto no se puede precomputar el espacio de 6 dígitos (rainbow table),
        a diferencia de un SHA-256 pelado, aunque se filtre la BD.
        """
        return hmac.new(
            self._secret_key.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
        ).hexdigest()
