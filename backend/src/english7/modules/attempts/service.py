from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Callable, Protocol
from uuid import UUID

from english7.api.errors import ApplicationError


class AttemptState(StrEnum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Attempt:
    id: UUID
    quiz_id: UUID
    status: AttemptState
    started_at: datetime
    duration_minutes: int


class Clock(Protocol):
    def current_time(self) -> datetime: ...


class AttemptRepository(Protocol):
    def get(self, attempt_id: UUID) -> Attempt | None: ...

    def save(self, attempt: Attempt) -> None: ...

    def save_answer(
        self, attempt_id: UUID, question_id: UUID, answer: dict
    ) -> None: ...

    def consume_audio_play(
        self, attempt_id: UUID, track_id: UUID, initial_plays: int
    ) -> int | None: ...


class AttemptService:
    def __init__(
        self,
        repository: AttemptRepository,
        clock: Clock,
        *,
        max_audio_plays: int,
    ) -> None:
        if max_audio_plays <= 0:
            raise ValueError("Maximum audio plays must be positive")
        self._repository = repository
        self._clock = clock
        self._max_audio_plays = max_audio_plays

    def _get(self, attempt_id: UUID) -> Attempt:
        attempt = self._repository.get(attempt_id)
        if attempt is None:
            raise ApplicationError("attempt_not_found", "Attempt was not found", 404)
        return attempt

    def resume(self, attempt_id: UUID) -> Attempt:
        attempt = self._get(attempt_id)
        deadline = attempt.started_at + timedelta(minutes=attempt.duration_minutes)
        if (
            attempt.status is AttemptState.IN_PROGRESS
            and self._clock.current_time() >= deadline
        ):
            attempt = replace(attempt, status=AttemptState.EXPIRED)
            self._repository.save(attempt)
        return attempt

    def _require_active(self, attempt_id: UUID) -> Attempt:
        attempt = self.resume(attempt_id)
        if attempt.status is not AttemptState.IN_PROGRESS:
            raise ApplicationError(
                "attempt_locked", "Submitted or expired attempts cannot change", 409
            )
        return attempt

    def save_answer(
        self, attempt_id: UUID, question_id: UUID, answer: dict
    ) -> None:
        self._require_active(attempt_id)
        self._repository.save_answer(attempt_id, question_id, answer)

    def play_audio(
        self,
        attempt_id: UUID,
        track_id: UUID,
        authorize_media: Callable[[], bool],
    ) -> int:
        self._require_active(attempt_id)
        if not authorize_media():
            raise ApplicationError(
                "media_forbidden", "Audio access is not authorized", 403
            )
        remaining = self._repository.consume_audio_play(
            attempt_id, track_id, self._max_audio_plays
        )
        if remaining is None:
            raise ApplicationError(
                "audio_play_limit_reached", "No audio plays remain", 409
            )
        return remaining
