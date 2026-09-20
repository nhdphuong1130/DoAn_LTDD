from uuid import uuid4

from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.textbooks.domain import (
    TextbookActivityDetail,
    TextbookFragment,
    TextbookSectionDetail,
    TextbookUnit,
    TextbookUnitStructure,
)
from english7.modules.textbooks.router import get_textbook_service


class FakeTextbookService:
    def __init__(self) -> None:
        self.unit = TextbookUnit(uuid4(), 1, "Hobbies", True)

    def list_units(self, offset: int, limit: int):
        assert offset == 0
        assert limit == 20
        return [self.unit]

    def get_unit_structure(self, unit_id):
        assert unit_id == self.unit.id
        return TextbookUnitStructure(
            id=self.unit.id,
            number=1,
            title="Hobbies",
            is_published=True,
            sections=[
                TextbookSectionDetail(
                    id=uuid4(),
                    unit_id=self.unit.id,
                    title="Getting Started",
                    section_type="lesson",
                    position=1,
                    activities=[
                        TextbookActivityDetail(
                            id=uuid4(),
                            section_id=uuid4(),
                            number="1",
                            activity_type="reading",
                            instruction="Listen and read.",
                            fragments=[],
                        )
                    ],
                )
            ],
        )


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


def test_student_gets_unit_structure(client) -> None:
    service = FakeTextbookService()
    student = AuthUser.new(
        email="student@example.com",
        password_hash="not-returned",
        role="student",
    )
    app.dependency_overrides[get_textbook_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: student
    try:
        response = client.get(f"/api/v1/lessons/{service.unit.id}/structure")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["number"] == 1
    assert data["title"] == "Hobbies"
    assert len(data["sections"]) == 1
    assert data["sections"][0]["title"] == "Getting Started"
    assert data["sections"][0]["activities"][0]["instruction"] == "Listen and read."

