from uuid import uuid4

from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.quizzes.domain import QuizDraft, QuizOptions
from english7.modules.quizzes.router import get_quiz_service


class FakeQuizService:
    def __init__(self):
        self.calls = []

    def generate(self, user_id, duration_minutes, difficulty):
        self.calls.append((user_id, duration_minutes, difficulty))
        return QuizDraft(uuid4(), duration_minutes, difficulty, 20)

    def options(self):
        return QuizOptions((15, 45, 60), 10, 90, 2)


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


def test_student_reads_quiz_policy_options_from_server(client) -> None:
    student = AuthUser.new(
        email="student@example.com", password_hash="unused", role="student"
    )
    service = FakeQuizService()
    app.dependency_overrides[get_current_user] = lambda: student
    app.dependency_overrides[get_quiz_service] = lambda: service
    try:
        response = client.get("/api/v1/quizzes/options")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "preset_durations": [15, 45, 60],
        "custom_minimum_minutes": 10,
        "custom_maximum_minutes": 90,
        "max_audio_plays": 2,
    }


def test_student_submits_quiz_without_answers_scores_zero(client) -> None:
    student = AuthUser.new(
        email="student@example.com", password_hash="unused", role="student"
    )
    quiz_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: student
    try:
        response = client.post(f"/api/v1/quizzes/{quiz_id}/submit", json={"answers": {}})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["correct"] == 0

