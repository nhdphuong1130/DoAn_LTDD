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


def test_register_login_and_me_flow(client) -> None:
    service = AuthService(
        MemoryAuthRepository(),
        PasswordHasher(),
        TokenService(
            secret="test-secret-with-sufficient-length",
            algorithm="HS256",
            lifetime=timedelta(minutes=30),
            clock=lambda: datetime(2026, 9, 18, tzinfo=timezone.utc),
        ),
    )
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

