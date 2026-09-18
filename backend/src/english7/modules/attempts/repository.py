from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from english7.db.models import (
    Quiz,
    QuizBlueprint,
    StudentAnswer,
    TestAttempt,
)
from english7.modules.attempts.service import Attempt, AttemptState


class SQLAlchemyAttemptRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def get(self, attempt_id: UUID) -> Attempt | None:
        with self._session_factory() as session:
            row = session.execute(
                select(TestAttempt, QuizBlueprint.duration_minutes)
                .join(Quiz, Quiz.id == TestAttempt.quiz_id)
                .join(QuizBlueprint, QuizBlueprint.id == Quiz.blueprint_id)
                .where(TestAttempt.id == attempt_id)
            ).one_or_none()
            if row is None:
                return None
            attempt, duration = row
            return Attempt(
                attempt.id,
                attempt.quiz_id,
                AttemptState(attempt.status),
                attempt.created_at,
                duration,
            )

    def save(self, attempt: Attempt) -> None:
        with self._session_factory() as session, session.begin():
            row = session.get(TestAttempt, attempt.id)
            if row is None:
                raise KeyError(attempt.id)
            row.status = attempt.status.value

    def save_answer(
        self, attempt_id: UUID, question_id: UUID, answer: dict
    ) -> None:
        with self._session_factory() as session, session.begin():
            row = session.scalar(
                select(StudentAnswer).where(
                    StudentAnswer.test_attempt_id == attempt_id,
                    StudentAnswer.question_id == question_id,
                )
            )
            if row is None:
                session.add(
                    StudentAnswer(
                        test_attempt_id=attempt_id,
                        question_id=question_id,
                        answer_payload=answer,
                    )
                )
            else:
                row.answer_payload = answer

    def consume_audio_play(
        self, attempt_id: UUID, track_id: UUID, initial_plays: int
    ) -> int | None:
        with self._session_factory() as session, session.begin():
            now = datetime.now(timezone.utc)
            remaining = session.execute(
                text(
                    """
                    MERGE audio_playbacks WITH (HOLDLOCK) AS target
                    USING (
                        SELECT :attempt_id AS test_attempt_id,
                               :track_id AS audio_track_id
                    ) AS source
                    ON target.test_attempt_id = source.test_attempt_id
                       AND target.audio_track_id = source.audio_track_id
                    WHEN MATCHED AND target.remaining_plays > 0 THEN
                        UPDATE SET remaining_plays = target.remaining_plays - 1,
                                   updated_at = :now
                    WHEN NOT MATCHED THEN
                        INSERT (
                            id, test_attempt_id, audio_track_id, remaining_plays,
                            created_at, updated_at
                        )
                        VALUES (
                            :playback_id, :attempt_id, :track_id,
                            :remaining_after_first, :now, :now
                        )
                    OUTPUT inserted.remaining_plays;
                    """
                ),
                {
                    "attempt_id": attempt_id,
                    "track_id": track_id,
                    "playback_id": uuid4(),
                    "remaining_after_first": initial_plays - 1,
                    "now": now,
                },
            )
            return remaining.scalar_one_or_none()
