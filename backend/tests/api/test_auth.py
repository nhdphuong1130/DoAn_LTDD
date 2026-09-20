from dataclasses import replace
from datetime import datetime, timedelta, timezone

from english7.core.security import PasswordHasher, TokenService
from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_auth_service
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


def configured_service() -> AuthService:
    return AuthService(
        MemoryAuthRepository(),
        PasswordHasher(),
        TokenService(
            secret="test-secret-with-sufficient-length",
            algorithm="HS256",
            lifetime=timedelta(minutes=30),
            clock=lambda: datetime(2026, 9, 18, tzinfo=timezone.utc),
        ),
    )


def test_register_login_and_me_flow(client) -> None:
    service = configured_service()
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        register = client.post(
            "/api/v1/auth/register",
            json={"email": "student@example.com", "password": "secure-password"},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "student@example.com", "password": "secure-password"},
        )
        token = login.json()["access_token"]
        profile = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert register.status_code == 201
    assert login.status_code == 200
    assert profile.status_code == 200
    assert profile.json()["email"] == "student@example.com"
    assert profile.json()["role"] == "student"


def test_me_rejects_missing_token(client) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_authenticated_user_can_read_and_update_only_own_profile(client) -> None:
    service = configured_service()
    user = service.register("student@example.com", "secure-password")
    token = service.token_service.issue(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        updated = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Nguyễn An",
                "date_of_birth": "2013-05-10",
                "gender": "female",
                "school_name": "THCS Nguyễn Du",
                "class_name": "7A1",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Nguyễn An"
    assert updated.json()["email"] == "student@example.com"
    assert "password_hash" not in updated.json()


def test_change_password_returns_no_content(client) -> None:
    service = configured_service()
    user = service.register("student@example.com", "secure-password")
    token = service.token_service.issue(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "secure-password",
                "new_password": "new-secure-password",
                "confirm_password": "new-secure-password",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""


def test_profile_update_requires_authentication(client) -> None:
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "Nguyễn An"},
    )

    assert response.status_code == 401


def test_profile_update_rejects_invalid_gender(client) -> None:
    service = configured_service()
    user = service.register("student@example.com", "secure-password")
    token = service.token_service.issue(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"gender": "invalid"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_profile_update_rejects_account_fields(client) -> None:
    service = configured_service()
    user = service.register("student@example.com", "secure-password")
    token = service.token_service.issue(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        response = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": "attacker@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_change_password_rejects_mismatched_confirmation(client) -> None:
    service = configured_service()
    user = service.register("student@example.com", "secure-password")
    token = service.token_service.issue(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "secure-password",
                "new_password": "new-secure-password",
                "confirm_password": "different-password",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["code"] == "password_confirmation_mismatch"
