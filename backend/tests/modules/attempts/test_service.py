from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.modules.attempts.service import (
    Attempt,
    AttemptService,
    AttemptState,
)


class FixedClock:
    def __init__(self, now):
        self.now = now

    def current_time(self):
        return self.now


class FakeAttemptRepository:
    def __init__(self, attempt):
        self.attempt = attempt
        self.remaining = {}
        self.consume_calls = 0

    def get(self, attempt_id):
        assert attempt_id == self.attempt.id
        return self.attempt

    def save(self, attempt):
        self.attempt = attempt

    def consume_audio_play(self, attempt_id, track_id, initial_plays):
        self.consume_calls += 1
        key = (attempt_id, track_id)
        current = self.remaining.setdefault(key, initial_plays)
        if current <= 0:
            return None
        self.remaining[key] = current - 1
        return current - 1


def build(status=AttemptState.IN_PROGRESS, elapsed_minutes=0):
    started = datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc)
    attempt = Attempt(uuid4(), uuid4(), status, started, 45)
    clock = FixedClock(started + timedelta(minutes=elapsed_minutes))
    repository = FakeAttemptRepository(attempt)
    return AttemptService(repository, clock, max_audio_plays=2), repository, attempt


def test_submitted_attempt_cannot_mutate() -> None:
    service, _, attempt = build(AttemptState.SUBMITTED)

    with pytest.raises(ApplicationError) as captured:
        service.save_answer(attempt.id, uuid4(), {"choice": "A"})

    assert captured.value.code == "attempt_locked"


def test_server_clock_auto_submits_expired_attempt() -> None:
    service, repository, attempt = build(elapsed_minutes=46)

    resumed = service.resume(attempt.id)

    assert resumed.status is AttemptState.EXPIRED
    assert repository.attempt.status is AttemptState.EXPIRED


def test_audio_has_two_plays_and_never_resets_when_resumed() -> None:
    service, _, attempt = build()
    track = uuid4()

    assert service.play_audio(attempt.id, track, lambda: True) == 1
    service.resume(attempt.id)
    assert service.play_audio(attempt.id, track, lambda: True) == 0

    with pytest.raises(ApplicationError) as captured:
        service.play_audio(attempt.id, track, lambda: True)
    assert captured.value.code == "audio_play_limit_reached"


def test_failed_media_authorization_does_not_decrement_play_count() -> None:
    service, repository, attempt = build()

    with pytest.raises(ApplicationError) as captured:
        service.play_audio(attempt.id, uuid4(), lambda: False)

    assert captured.value.code == "media_forbidden"
    assert repository.consume_calls == 0
