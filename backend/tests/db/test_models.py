from uuid import uuid4

import pytest
from sqlalchemy import Unicode

from english7.db.models import (
    AudioPlayback,
    QuizQuestion,
    ReviewStatus,
    SourceFragment,
    User,
)


def test_user_profile_text_columns_are_nullable_unicode() -> None:
    columns = User.__table__.c

    assert isinstance(columns.full_name.type, Unicode)
    assert isinstance(columns.school_name.type, Unicode)
    assert isinstance(columns.class_name.type, Unicode)
    assert columns.full_name.nullable is True
    assert columns.date_of_birth.nullable is True


def test_source_fragment_cannot_publish_before_verification() -> None:
    fragment = SourceFragment(
        source_document_id=uuid4(),
        pdf_page=8,
        printed_page=6,
        x=0,
        y=0,
        width=100,
        height=50,
        normalized_text="Hobbies are activities we do for pleasure.",
    )

    with pytest.raises(ValueError, match="verified"):
        fragment.publish()


def test_verified_source_fragment_can_be_published() -> None:
    fragment = SourceFragment(
        source_document_id=uuid4(),
        pdf_page=8,
        printed_page=6,
        x=0,
        y=0,
        width=100,
        height=50,
        normalized_text="Hobbies are activities we do for pleasure.",
        review_status=ReviewStatus.VERIFIED,
    )

    fragment.publish()

    assert fragment.is_published is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pdf_page", -1),
        ("printed_page", -1),
        ("x", -1),
        ("y", -1),
        ("width", -1),
        ("height", -1),
    ],
)
def test_source_fragment_rejects_negative_geometry(field: str, value: int) -> None:
    values = {
        "source_document_id": uuid4(),
        "pdf_page": 8,
        "printed_page": 6,
        "x": 0,
        "y": 0,
        "width": 100,
        "height": 50,
        "normalized_text": "Verified textbook text",
    }
    values[field] = value

    with pytest.raises(ValueError, match=field):
        SourceFragment(**values)


def test_quiz_question_requires_source_before_publish() -> None:
    question = QuizQuestion(
        quiz_id=uuid4(),
        prompt="Which activity is a hobby?",
        answer_payload={"correct": "gardening"},
    )

    with pytest.raises(ValueError, match="source"):
        question.publish()


def test_audio_playback_never_becomes_negative() -> None:
    playback = AudioPlayback(
        test_attempt_id=uuid4(),
        audio_track_id=uuid4(),
        remaining_plays=1,
    )

    playback.consume_play()
    assert playback.remaining_plays == 0

    with pytest.raises(ValueError, match="No audio plays"):
        playback.consume_play()
