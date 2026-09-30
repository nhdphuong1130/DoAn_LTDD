from datetime import timezone
from sqlalchemy import func, select, update
from english7.api.errors import ApplicationError
from english7.db.models import User
from english7.modules.speaking.models import SpeakingAttempt, SpeakingPreference


class SpeakingRepository:
    def __init__(self, factory):
        self.factory = factory

    @staticmethod
    def serialize(row):
        created = row.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return {'id': str(row.id), 'card_id': str(row.card_id), 'prompt': row.prompt,
                'transcript': row.transcript, 'source_label': row.source_label,
                'created_at': created.isoformat(), **row.result}

    @staticmethod
    def _existing(session, user_id, request_id, digest=None):
        row = session.get(SpeakingAttempt, request_id)
        if row is None:
            return None
        if row.user_id != user_id:
            raise ApplicationError('attempt_not_found', 'Attempt was not found', 404)
        if digest is not None and row.request_hash != digest:
            raise ApplicationError('request_conflict', 'Use a new request ID for a different recording', 409)
        return row

    def existing(self, user_id, request_id, digest):
        with self.factory() as session:
            row = self._existing(session, user_id, request_id, digest)
            return self.serialize(row) if row else None

    def save(self, user_id, request_id, card_id, digest, voice, model, prompt, transcript, source, result):
        with self.factory() as session, session.begin():
            # Serialize inserts for this user across API workers on SQL Server.
            session.execute(update(User).where(User.id == user_id).values(is_active=User.is_active))
            previous = self._existing(session, user_id, request_id, digest)
            if previous:
                return self.serialize(previous)
            row = SpeakingAttempt(id=request_id, user_id=user_id, card_id=card_id,
                                  request_hash=digest, voice_id=voice, model=model,
                                  prompt=prompt, transcript=transcript, source_label=source, result=result)
            session.add(row)
            session.flush()
            return self.serialize(row)

    def get(self, user_id, attempt_id):
        with self.factory() as session:
            row = self._existing(session, user_id, attempt_id)
            if row is None:
                raise ApplicationError('attempt_not_found', 'Attempt was not found', 404)
            return self.serialize(row), row.voice_id

    def history(self, user_id):
        with self.factory() as session:
            rows = session.scalars(select(SpeakingAttempt).where(SpeakingAttempt.user_id == user_id)
                                   .order_by(SpeakingAttempt.created_at.desc(), SpeakingAttempt.id).limit(50))
            return [self.serialize(row) for row in rows]

    def count(self, user_id):
        with self.factory() as session:
            return session.scalar(select(func.count()).select_from(SpeakingAttempt)
                                  .where(SpeakingAttempt.user_id == user_id))

    def voice(self, user_id):
        with self.factory() as session:
            row = session.get(SpeakingPreference, user_id)
            return row.voice_id if row else None

    def set_voice(self, user_id, voice):
        with self.factory() as session, session.begin():
            session.execute(update(User).where(User.id == user_id).values(is_active=User.is_active))
            row = session.get(SpeakingPreference, user_id)
            if row:
                row.voice_id = voice
            else:
                session.add(SpeakingPreference(user_id=user_id, voice_id=voice))
