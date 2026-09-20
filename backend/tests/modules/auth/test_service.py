from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

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

    def update_profile(
        self,
        user_id,
        changes: dict[str, object],
    ) -> AuthUser | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        updated = replace(user, **changes)
        self.users[user.email] = updated
        return updated

    def update_password_hash(self, user_id, password_hash: str) -> bool:
        user = self.get_by_id(user_id)
        if user is None:
            return False
        self.users[user.email] = replace(user, password_hash=password_hash)
        return True


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


def test_update_profile_normalizes_optional_text() -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    updated = service.update_profile(
        user.id,
        {
            "full_name": "  Nguyễn An  ",
            "school_name": "   ",
            "class_name": " 7A1 ",
            "gender": "female",
            "date_of_birth": date(2013, 5, 10),
        },
    )

    assert updated.full_name == "Nguyễn An"
    assert updated.school_name is None
    assert updated.class_name == "7A1"


def test_update_profile_rejects_unknown_gender() -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    with pytest.raises(ApplicationError) as captured:
        service.update_profile(user.id, {"gender": "unknown"})

    assert captured.value.code == "profile_gender_invalid"


def test_change_password_requires_current_password_and_updates_login() -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    service.change_password(
        user.id,
        current_password="secure-password",
        new_password="new-secure-password",
        confirm_password="new-secure-password",
    )

    assert service.login("student@example.com", "new-secure-password")
    with pytest.raises(ApplicationError):
        service.login("student@example.com", "secure-password")


@pytest.mark.parametrize(
    ("current", "new", "confirmation", "code"),
    [
        (
            "wrong-password",
            "new-secure-password",
            "new-secure-password",
            "current_password_invalid",
        ),
        (
            "secure-password",
            "different-password",
            "mismatch-password",
            "password_confirmation_mismatch",
        ),
        (
            "secure-password",
            "secure-password",
            "secure-password",
            "password_unchanged",
        ),
    ],
)
def test_change_password_rejects_invalid_requests(
    current: str,
    new: str,
    confirmation: str,
    code: str,
) -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    with pytest.raises(ApplicationError) as captured:
        service.change_password(
            user.id,
            current_password=current,
            new_password=new,
            confirm_password=confirmation,
        )

    assert captured.value.code == code
