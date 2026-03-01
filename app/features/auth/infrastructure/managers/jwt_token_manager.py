from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.core.exceptions.exceptions import InvalidCredentialsException
from app.features.auth.application.contracts.token_manager import TokenManager


class JwtTokenManager(TokenManager):
    _ALGORITHM = "HS256"
    _ACCESS_MINUTES = 15
    _REFRESH_DAYS = 7

    def __init__(self, secret_key: str) -> None:
        if not secret_key.strip():
            raise ValueError("JWT secret key is empty")
        self._secret = secret_key

    def create_access_token(self, subject: str, claims: dict[str, Any] | None = None) -> str:
        return self._encode_token(
            subject=subject,
            token_type="access",
            ttl=timedelta(minutes=self._ACCESS_MINUTES),
            claims=claims,
        )

    def create_refresh_token(self, subject: str, claims: dict[str, Any] | None = None) -> str:
        return self._encode_token(
            subject=subject,
            token_type="refresh",
            ttl=timedelta(days=self._REFRESH_DAYS),
            claims=claims,
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        payload = self._decode_token(token)
        if payload.get("token_type") != "access":
            raise InvalidCredentialsException()
        return payload

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        payload = self._decode_token(token)
        if payload.get("token_type") != "refresh":
            raise InvalidCredentialsException()
        return payload

    def _encode_token(
        self,
        subject: str,
        token_type: str,
        ttl: timedelta,
        claims: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": subject,
            "token_type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + ttl).timestamp()),
        }
        if claims:
            payload.update(claims)
        return jwt.encode(payload, self._secret, algorithm=self._ALGORITHM)

    def _decode_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._ALGORITHM])
        except InvalidTokenError as exc:
            raise InvalidCredentialsException() from exc
        return dict(payload)
