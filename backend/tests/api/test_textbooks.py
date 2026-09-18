from uuid import uuid4

from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.textbooks.domain import TextbookUnit
from english7.modules.textbooks.router import get_textbook_service


class FakeTextbookService:
    def __init__(self) -> None:
        self.unit = TextbookUnit(uuid4(), 1, "Hobbies", True)

    def list_units(self, offset: int, limit: int):
        assert offset == 0
        assert limit == 20
        return [self.unit]


def test_student_lists_published_textbook_units(client) -> None:
    service = FakeTextbookService()
    student = AuthUser.new(
        email="student@example.com",
        password_hash="not-returned",
        role="student",
    )
    app.dependency_overrides[get_textbook_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: student
    try:
        response = client.get("/api/v1/textbooks/units")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["title"] == "Hobbies"
    assert response.json()["pagination"] == {"offset": 0, "limit": 20, "count": 1}

