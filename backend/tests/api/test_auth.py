import json
from unittest.mock import MagicMock, patch

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from english7.core.security import PasswordHasher, TokenService
from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_auth_service, get_sms_service
from english7.modules.auth.service import AuthService
from english7.modules.auth.sms_service import SmsOtpService


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


def test_otp_send_and_verify_flow(client) -> None:
    service = configured_service()
    service.register_phone("0365218732", "SecurePass123!")
    sms_service = SmsOtpService(
        account_sid="fake_sid",
        auth_token=None,
        from_phone="+1234567890",
    )
    app.dependency_overrides[get_auth_service] = lambda: service
    app.dependency_overrides[get_sms_service] = lambda: sms_service
    try:
        send_resp = client.post(
            "/api/v1/auth/otp/send",
            json={"phone": "0365218732"},
        )
        assert send_resp.status_code == 200
        assert send_resp.json()["status"] == "success"

        stored_code = sms_service._store["+84365218732"][0]

        verify_resp = client.post(
            "/api/v1/auth/otp/verify",
            json={"phone": "0365218732", "otp": stored_code},
        )
        assert verify_resp.status_code == 200
        token = verify_resp.json()["access_token"]

        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "phone_84365218732@english7.edu.vn"
    finally:
        app.dependency_overrides.clear()


def test_otp_verify_rejects_invalid_otp(client) -> None:
    service = configured_service()
    service.register_phone("0365218732", "SecurePass123!")
    sms_service = SmsOtpService(
        account_sid="fake_sid",
        auth_token=None,
        from_phone="+1234567890",
    )
    app.dependency_overrides[get_auth_service] = lambda: service
    app.dependency_overrides[get_sms_service] = lambda: sms_service
    try:
        client.post(
            "/api/v1/auth/otp/send",
            json={"phone": "0365218732"},
        )
        verify_resp = client.post(
            "/api/v1/auth/otp/verify",
            json={"phone": "0365218732", "otp": "000000"},
        )
        assert verify_resp.status_code == 400
        assert verify_resp.json()["code"] == "invalid_otp"
    finally:
        app.dependency_overrides.clear()


def test_otp_send_voice_channel(client) -> None:
    service = configured_service()
    service.register_phone("0365218732", "SecurePass123!")
    sms_service = SmsOtpService(
        account_sid="fake_sid",
        auth_token=None,
        from_phone="+1234567890",
        clicksend_username="user",
        clicksend_api_key="key",
    )
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"http_code": 200}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        app.dependency_overrides[get_auth_service] = lambda: service
        app.dependency_overrides[get_sms_service] = lambda: sms_service
        try:
            send_resp = client.post(
                "/api/v1/auth/otp/send",
                json={"phone": "0365218732", "channel": "voice"},
            )
            assert send_resp.status_code == 200
            assert "cuộc gọi thoại" in send_resp.json()["message"]
        finally:
            app.dependency_overrides.clear()


def test_otp_send_purpose_validation(client) -> None:
    service = configured_service()
    sms_service = SmsOtpService(account_sid="fake_sid", auth_token=None, from_phone="+1234567890")
    app.dependency_overrides[get_auth_service] = lambda: service
    app.dependency_overrides[get_sms_service] = lambda: sms_service
    try:
        # 1. Reset password on non-existent phone fails 404
        resp = client.post("/api/v1/auth/otp/send", json={"phone": "0374423251", "purpose": "reset_password"})
        assert resp.status_code == 404
        assert resp.json()["code"] == "phone_not_found"

        # 2. Both new and existing phone succeed for OTP send (unified login/register)
        resp2 = client.post("/api/v1/auth/otp/send", json={"phone": "0374423251", "purpose": "register"})
        assert resp2.status_code == 200

        # Create user
        service.register_phone("0374423251", "Password123!")

        # 3. Existing user cannot re-register (returns 409 phone_already_registered)
        resp_conflict = client.post("/api/v1/auth/otp/send", json={"phone": "0374423251", "purpose": "register"})
        assert resp_conflict.status_code == 409
        assert resp_conflict.json()["code"] == "phone_already_registered"

        # 4. Existing user can send OTP for login without conflict error
        resp3 = client.post("/api/v1/auth/otp/send", json={"phone": "0374423251", "purpose": "login"})
        assert resp3.status_code == 200

        # 5. Reset password purpose succeeds 200
        resp4 = client.post("/api/v1/auth/otp/send", json={"phone": "0374423251", "purpose": "reset_password"})
        assert resp4.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_register_phone_and_reset_password_api(client) -> None:
    service = configured_service()
    sms_service = SmsOtpService(account_sid="fake_sid", auth_token=None, from_phone="+1234567890")
    app.dependency_overrides[get_auth_service] = lambda: service
    app.dependency_overrides[get_sms_service] = lambda: sms_service
    try:
        # Send OTP
        client.post("/api/v1/auth/otp/send", json={"phone": "0374423251", "purpose": "register"})
        target = "+84374423251"
        code, _ = sms_service._store[target]

        # Register phone user
        reg_resp = client.post(
            "/api/v1/auth/register-phone",
            json={"phone": "0374423251", "otp": code, "password": "OriginalPassword123!"},
        )
        assert reg_resp.status_code == 201
        assert "access_token" in reg_resp.json()

        # Send OTP for reset password
        client.post("/api/v1/auth/otp/send", json={"phone": "0374423251", "purpose": "reset_password"})
        reset_code, _ = sms_service._store[target]

        # Reset password
        reset_resp = client.post(
            "/api/v1/auth/reset-password",
            json={
                "phone": "0374423251",
                "otp": reset_code,
                "new_password": "NewResetPassword123!",
                "confirm_password": "NewResetPassword123!",
            },
        )
        assert reset_resp.status_code == 200
        assert "thành công" in reset_resp.json()["message"]

        # Login with new password
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "0374423251", "password": "NewResetPassword123!"},
        )
        assert login_resp.status_code == 200
    finally:
        app.dependency_overrides.clear()



