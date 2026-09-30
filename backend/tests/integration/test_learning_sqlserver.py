"""Live-database smoke test; all test records are rolled back, never committed."""
from uuid import uuid4
import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from english7.db.models import Role, User
from english7.db.session import get_engine
from english7.modules.flashcards.repository import SQLAlchemyFlashcardRepository
from english7.modules.flashcards.service import FlashcardService
from english7.modules.speaking.repository import SpeakingRepository
from english7.modules.speaking.service import SpeakingService
from english7.modules.speaking.runtime import LocalSpeechRuntime
from english7.core.settings import get_settings


class SpeechStub:
    def voices(self):
        return [{'id': 'test', 'name': 'Test voice'}]

    def transcribe(self, audio):
        return {'transcript': 'reading', 'model': 'integration-stub'}


def test_learning_transactions_on_live_database():
    with get_engine().connect() as connection:
        transaction = connection.begin()
        factory = sessionmaker(connection, expire_on_commit=False, join_transaction_mode='rollback_only')
        try:
            user_id = uuid4()
            with factory.begin() as session:
                role_id = session.scalar(select(Role.id).where(Role.name == 'student'))
                session.add(User(id=user_id, email=f'{user_id}@test.invalid', password_hash='test-only', role_id=role_id))
            cards = FlashcardService(SQLAlchemyFlashcardRepository(factory))
            clip = os.environ.get('ENGLISH7_TEST_SPEECH_FILE')
            runtime = LocalSpeechRuntime(get_settings().speech_runtime_url) if clip else SpeechStub()
            prompt = ('And so my fellow Americans ask not what your country can do for you '
                      'ask what you can do for your country') if clip else 'reading'
            recording = Path(clip).read_bytes() if clip else b'stub-audio'
            voice = runtime.voices()[0]['id']
            speech = SpeakingService(SpeakingRepository(factory), cards, runtime)
            deck = cards.create_deck(user_id, 'Bộ kiểm thử')
            card = cards.create_card(user_id, deck.id, word=prompt, meaning='đọc sách')
            assert cards.list_cards(user_id, deck.id)[0].meaning == 'đọc sách'
            request = uuid4()
            review = cards.review(user_id, card.id, request_id=request, answer=prompt, rating='good')
            assert review.correct
            assert cards.review(user_id, card.id, request_id=request, answer=prompt, rating='good') == review
            assert not cards.review_queue(user_id, deck.id)
            speech.set_voice(user_id, voice)
            attempt = uuid4()
            result = speech.submit(user_id, attempt, card.id, voice, recording)
            assert result['match_percent'] == 100
            assert speech.submit(user_id, attempt, card.id, voice, recording) == result
            assert speech.voices(user_id)['selected_voice'] == voice
            if clip:
                assert speech.feedback_audio(user_id, attempt).startswith(b'RIFF')
                print('Real ASR word match:', result['match_percent'], 'Feedback WAV received')
            assert speech.progress(user_id)['reviewed_cards'] == 1
            assert speech.progress(user_id)['speaking_count'] == 1
            cards.delete_deck(user_id, deck.id)
            assert speech.history(user_id)[0]['prompt'] == prompt
        finally:
            transaction.rollback()
