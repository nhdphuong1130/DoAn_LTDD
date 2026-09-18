from uuid import uuid4

from english7.db.models import ReviewStatus
from english7.main import app
from english7.modules.admin.router import get_admin_textbook_service
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.textbooks.domain import TextbookFragment


class FakeAdminService:
    def __init__(self, fragment_id, unit_id) -> None:
        self.fragment_id = fragment_id
        self.unit_id = unit_id

    def verify_fragment(self, fragment_id, corrected_text, reviewer_id):
        assert fragment_id == self.fragment_id
        return TextbookFragment(
            id=fragment_id,
            unit_id=self.unit_id,
            pdf_page=10,
            printed_page=8,
            normalized_text=corrected_text,
            review_status=ReviewStatus.VERIFIED,
            is_published=True,
            reviewer_id=reviewer_id,
        )


def test_admin_verifies_fragment(client) -> None:
    fragment_id = uuid4()
    admin = AuthUser.new(
        email="admin@example.com",
        password_hash="not-returned",
        role="admin",
    )
    app.dependency_overrides[get_admin_textbook_service] = lambda: FakeAdminService(
        fragment_id,
        uuid4(),
    )
    app.dependency_overrides[get_current_user] = lambda: admin
    try:
        response = client.patch(
            f"/api/v1/admin/fragments/{fragment_id}/verify",
            json={"normalized_text": "Hobbies are fun."},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["review_status"] == "verified"
    assert response.json()["is_published"] is True


def test_student_cannot_verify_fragment(client) -> None:
    student = AuthUser.new(
        email="student@example.com",
        password_hash="not-returned",
        role="student",
    )
    app.dependency_overrides[get_admin_textbook_service] = lambda: FakeAdminService(
        uuid4(),
        uuid4(),
    )
    app.dependency_overrides[get_current_user] = lambda: student
    try:
        response = client.patch(
            f"/api/v1/admin/fragments/{uuid4()}/verify",
            json={"normalized_text": "Hobbies are fun."},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"

