from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from english7.api.errors import ApplicationError
from english7.modules.auth.domain import AuthUser, TokenClaims


def system_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PasswordHasher:
    def __init__(self) -> None:
        self._hasher = Argon2PasswordHasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, encoded: str) -> bool:
        try:
            return self._hasher.verify(encoded, password)
        except (VerifyMismatchError, InvalidHashError):
            return False


class TokenService:
    def __init__(
        self,
        *,
        secret: str | None,
        algorithm: str | None,
        lifetime: timedelta | None,
        clock: Callable[[], datetime] = system_utc_now,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._lifetime = lifetime
        self._clock = clock

    def _configuration(self) -> tuple[str, str, timedelta]:
        if not self._secret or not self._algorithm or self._lifetime is None:
            raise RuntimeError("JWT configuration is incomplete")
        return self._secret, self._algorithm, self._lifetime

    def issue(self, user: AuthUser) -> str:
        secret, algorithm, lifetime = self._configuration()
        now = self._clock()
        payload: dict[str, Any] = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "iat": now,
            "exp": now + lifetime,
        }
        return jwt.encode(payload, secret, algorithm=algorithm)

    def decode(self, encoded: str) -> TokenClaims:
        secret, algorithm, _ = self._configuration()
        try:
            payload = jwt.decode(
                encoded,
                secret,
                algorithms=[algorithm],
                options={"verify_exp": False},
            )
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            if expires_at <= self._clock():
                raise ApplicationError(
                    code="token_expired",
                    message="Access token has expired",
                    status_code=401,
                )
            return TokenClaims(
                subject=UUID(payload["sub"]),
                email=payload["email"],
                role=payload["role"],
            )
        except ApplicationError:
            raise
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
            raise ApplicationError(
                code="invalid_token",
                message="Access token is invalid",
                status_code=401,
            ) from error
