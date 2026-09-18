from datetime import datetime, timedelta, timezone

import pytest

from english7.api.errors import ApplicationError
from english7.core.security import PasswordHasher, TokenService
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.service import AuthService


class MemoryAuthRepository:
    def __init__(self) -> None:
        self.users: dict[str, AuthUser] = {}

    def get_by_email(self, email: str) -> AuthUser | None:
        return self.users.get(email)

    def get_by_id(self, user_id):
        return next(
            (user for user in self.users.values() if user.id == user_id),
            None,
        )

    def create(self, user: AuthUser) -> AuthUser:
        self.users[user.email] = user
        return user


def build_service(clock=lambda: datetime(2026, 9, 18, tzinfo=timezone.utc)):
    repository = MemoryAuthRepository()
    hasher = PasswordHasher()
    tokens = TokenService(
        secret="test-secret-with-sufficient-length",
        algorithm="HS256",
        lifetime=timedelta(minutes=30),
        clock=clock,
    )
    return AuthService(repository, hasher, tokens), repository, tokens


def test_password_hashing_round_trip() -> None:
    hasher = PasswordHasher()
    encoded = hasher.hash("correct horse battery staple")

    assert encoded != "correct horse battery staple"
    assert hasher.verify("correct horse battery staple", encoded) is True
    assert hasher.verify("wrong password", encoded) is False


def test_register_and_login_returns_access_token() -> None:
    service, _, tokens = build_service()
    registered = service.register("Student@Example.com", "secure-password")

    access_token = service.login("student@example.com", "secure-password")
    claims = tokens.decode(access_token)

    assert registered.email == "student@example.com"
    assert registered.role == "student"
    assert claims.subject == registered.id


def test_login_rejects_invalid_credentials() -> None:
    service, _, _ = build_service()
    service.register("student@example.com", "secure-password")

    with pytest.raises(ApplicationError) as error:
        service.login("student@example.com", "wrong-password")

    assert error.value.code == "invalid_credentials"


def test_expired_access_token_is_rejected() -> None:
    current = datetime(2026, 9, 18, tzinfo=timezone.utc)
    service, _, tokens = build_service(clock=lambda: current)
    user = service.register("student@example.com", "secure-password")
    encoded = tokens.issue(user)
    current += timedelta(minutes=31)

    with pytest.raises(ApplicationError) as error:
        tokens.decode(encoded)

    assert error.value.code == "token_expired"


def test_student_is_forbidden_from_admin_role() -> None:
    service, _, _ = build_service()
    student = service.register("student@example.com", "secure-password")

    with pytest.raises(ApplicationError) as error:
        service.authorize(student, {"admin"})

    assert error.value.status_code == 403


def test_admin_is_allowed_for_admin_role() -> None:
    service, repository, _ = build_service()
    admin = AuthUser.new(
        email="admin@example.com",
        password_hash=PasswordHasher().hash("secure-password"),
        role="admin",
    )
    repository.create(admin)

    assert service.authorize(admin, {"admin"}) is admin

