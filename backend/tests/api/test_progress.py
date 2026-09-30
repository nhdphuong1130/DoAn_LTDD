from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from english7.db.base import Base
from english7.db.models import Quiz, QuizBlueprint, QuizQuestion, TestAttempt as Attempt
from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.quizzes import router


@pytest.fixture
def quiz_data(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine)
    user = AuthUser.new(email='progress@example.com', password_hash='unused', role='student')
    quiz_id, question_id = uuid4(), uuid4()
    with factory.begin() as session:
        blueprint = QuizBlueprint(name='Test', duration_minutes=15, difficulty='adaptive', policy={})
        session.add(blueprint)
        session.flush()
        session.add(Quiz(id=quiz_id, blueprint_id=blueprint.id, created_for_user_id=user.id))
        session.add(QuizQuestion(id=question_id, quiz_id=quiz_id, prompt='Test', answer_payload={'correct': 'True'}))
        session.add(QuizQuestion(quiz_id=quiz_id, prompt='Unanswered', answer_payload={'correct': 'False'}))
    monkeypatch.setattr(router, 'get_session_factory', lambda: factory)
    app.dependency_overrides[get_current_user] = lambda: user
    yield user, quiz_id, question_id, factory
    app.dependency_overrides.clear()
    engine.dispose()


def test_submission_persists_and_progress_survives_next_request(client, quiz_data):
    _, quiz_id, question_id, factory = quiz_data
    assert client.get('/api/v1/quizzes/progress').json()['completed_quizzes'] == 0
    response = client.post(f'/api/v1/quizzes/{quiz_id}/submit', json={'answers': {str(question_id): ' true '}})
    assert response.json() == {'correct': 1, 'total': 2}
    progress = client.get('/api/v1/quizzes/progress').json()
    assert progress['completed_quizzes'] == 1
    assert progress['correct'] == 1
    assert progress['total'] == 2
    assert progress['history'][0]['quiz_id'] == str(quiz_id)
    assert progress['history'][0]['submitted_at']
    # Retrying the same submission cannot inflate progress or change the score.
    assert client.post(f'/api/v1/quizzes/{quiz_id}/submit', json={'answers': {}}).json() == response.json()
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Attempt)) == 1


def test_other_student_cannot_submit_or_see_results(client, quiz_data):
    _, quiz_id, _, _ = quiz_data
    client.post(f'/api/v1/quizzes/{quiz_id}/submit', json={'answers': {}})
    other = AuthUser.new(email='other@example.com', password_hash='unused', role='student')
    app.dependency_overrides[get_current_user] = lambda: other
    assert client.post(f'/api/v1/quizzes/{quiz_id}/submit', json={}).status_code == 404
    assert client.get('/api/v1/quizzes/progress').json()['completed_quizzes'] == 0


def test_unknown_quiz_has_no_fabricated_score(client, quiz_data):
    assert client.post(f'/api/v1/quizzes/{uuid4()}/submit', json={}).status_code == 404


def test_blank_submission_records_zero_and_all_questions(client, quiz_data):
    _, quiz_id, _, _ = quiz_data
    response = client.post(f'/api/v1/quizzes/{quiz_id}/submit', json={'answers': {}})
    assert response.json() == {'correct': 0, 'total': 2}
    assert client.get('/api/v1/quizzes/progress').json()['total'] == 2


def test_foreign_question_rejected_without_saving_attempt(client, quiz_data):
    _, quiz_id, _, factory = quiz_data
    assert client.post(f'/api/v1/quizzes/{quiz_id}/submit', json={'answers': {str(uuid4()): 'True'}}).status_code == 422
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Attempt)) == 0
        assert session.get(Quiz, quiz_id).is_locked is False


def test_progress_requires_authentication(client):
    assert client.get('/api/v1/quizzes/progress').status_code == 401


def test_non_student_is_rejected(client, quiz_data):
    app.dependency_overrides[get_current_user] = lambda: AuthUser.new(
        email='admin@example.com', password_hash='unused', role='admin')
    assert client.get('/api/v1/quizzes/progress').status_code == 403
