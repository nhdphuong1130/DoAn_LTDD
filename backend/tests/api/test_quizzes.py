from uuid import uuid4

from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.quizzes.domain import QuizDraft
from english7.modules.quizzes.router import get_quiz_service


class FakeQuizService:
    def __init__(self):
        self.calls = []

    def generate(self, user_id, duration_minutes, difficulty):
        self.calls.append((user_id, duration_minutes, difficulty))
        return QuizDraft(uuid4(), duration_minutes, difficulty, 20)


def test_student_requests_quiz_without_route_level_duration_rules(client) -> None:
    student = AuthUser.new(
        email="student@example.com", password_hash="unused", role="student"
    )
    service = FakeQuizService()
    app.dependency_overrides[get_current_user] = lambda: student
    app.dependency_overrides[get_quiz_service] = lambda: service
    try:
        response = client.post(
            "/api/v1/quizzes",
            json={"duration_minutes": 35, "difficulty": "adaptive"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["duration_minutes"] == 35
    assert service.calls == [(student.id, 35, "adaptive")]
