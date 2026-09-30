from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from english7.api.errors import ApplicationError
from english7.db.base import Base
from english7.db.models import Role, User
from english7.modules.speaking.repository import SpeakingRepository
from english7.modules.speaking.service import SpeakingService, compare_words


class Runtime:
    transcript = 'I enjoy reading'
    calls = 0
    def voices(self):
        return [{'id': 'voice-a', 'name': 'Voice A'}]
    def transcribe(self, audio):
        self.calls += 1
        return {'transcript': self.transcript, 'model': 'test-model'}
    def synthesize(self, text, voice_id):
        return b'RIFF-test'


class Cards:
    def get_card(self, user_id, card_id):
        return SimpleNamespace(word='I enjoy reading books.', source_label='[Unit 1, Page 10]')


@pytest.fixture
def setup_service():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory.begin() as session:
        role = Role(name='student')
        session.add(role)
        session.flush()
        user = User(email='learner@example.com', password_hash='x', role_id=role.id)
        session.add(user)
        session.flush()
        user_id = user.id
    runtime = Runtime()
    service = SpeakingService(SpeakingRepository(factory), Cards(), runtime)
    yield service, runtime, user_id
    engine.dispose()


def test_comparison_is_word_match_not_pronunciation():
    result = compare_words('I enjoy reading books.', 'i enjoy reading')
    assert result['match_percent'] == 75
    assert result['missing_words'] == ['books']
    assert result['extra_words'] == []
    assert compare_words('hello', 'hello extra')['match_percent'] == 0
    assert compare_words("I'm happy", "i’m happy")['match_percent'] == 100


def test_retry_persists_snapshot_without_retranscription(setup_service):
    service, runtime, user = setup_service
    request, card = uuid4(), uuid4()
    result = service.submit(user, request, card, 'voice-a', b'audio')
    assert result['match_percent'] == 75
    assert result['transcript'] == 'I enjoy reading'
    assert result == service.submit(user, request, card, 'voice-a', b'audio')
    assert runtime.calls == 1
    assert service.history(user) == [result]
    assert service.history(uuid4()) == []
    with pytest.raises(ApplicationError) as error:
        service.submit(user, request, card, 'voice-a', b'different')
    assert error.value.status_code == 409


def test_empty_audio_and_silence_do_not_save_attempt(setup_service):
    service, runtime, user = setup_service
    with pytest.raises(ApplicationError):
        service.submit(user, uuid4(), uuid4(), 'voice-a', b'')
    runtime.transcript = ''
    with pytest.raises(ApplicationError) as error:
        service.submit(user, uuid4(), uuid4(), 'voice-a', b'silence')
    assert error.value.status_code == 422
    assert service.history(user) == []


def test_voice_setting_and_audio_are_owner_scoped(setup_service):
    service, _, user = setup_service
    service.set_voice(user, 'voice-a')
    assert service.voices(user)['selected_voice'] == 'voice-a'
    with pytest.raises(ApplicationError):
        service.set_voice(user, 'fake')
    request = uuid4()
    service.submit(user, request, uuid4(), 'voice-a', b'audio')
    assert service.feedback_audio(user, request) == b'RIFF-test'
    with pytest.raises(ApplicationError) as error:
        service.feedback_audio(uuid4(), request)
    assert error.value.status_code == 404
