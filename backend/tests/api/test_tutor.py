from uuid import uuid4

from english7.main import app
from english7.modules.ai.contracts import Language
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.retrieval.service import Citation
from english7.modules.tutor.router import get_tutor_service
from english7.modules.tutor.service import TutorAnswer


class FakeTutorService:
    def __init__(self) -> None:
        self.calls = []

    def ask(self, question, language, *, user_id=None, upload_id=None):
        self.calls.append((question, language, user_id, upload_id))
        return TutorAnswer(
            answer="Tập thể dục mỗi ngày.",
            language=Language.VIETNAMESE,
            citations=(Citation(uuid4(), 22, 20),),
        )


def test_authenticated_student_asks_bilingual_tutor(client) -> None:
    fake = FakeTutorService()
    student = AuthUser.new(
        email="student@example.com", password_hash="unused", role="student"
    )
    app.dependency_overrides[get_current_user] = lambda: student
    app.dependency_overrides[get_tutor_service] = lambda: fake
    try:
        response = client.post(
            "/api/v1/tutor/ask",
            json={"question": "How can I stay healthy?", "language": "vi"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["language"] == "vi"
    assert response.json()["citations"][0]["printed_page"] == 20
    assert fake.calls == [
        ("How can I stay healthy?", Language.VIETNAMESE, student.id, None)
    ]


def test_student_can_ask_from_uploaded_image_without_typed_question(client) -> None:
    fake = FakeTutorService()
    student = AuthUser.new(
        email="student@example.com", password_hash="unused", role="student"
    )
    upload_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: student
    app.dependency_overrides[get_tutor_service] = lambda: fake
    try:
        response = client.post(
            "/api/v1/tutor/ask",
            json={"question": "", "language": "vi", "upload_id": str(upload_id)},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake.calls == [("", Language.VIETNAMESE, student.id, upload_id)]
