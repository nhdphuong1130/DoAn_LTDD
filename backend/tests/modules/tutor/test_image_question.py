from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.modules.ai.contracts import AIResponse, Language
from english7.modules.image_uploads.domain import ImageUploadRecord, ImageUploadStatus
from english7.modules.retrieval.service import (
    Citation,
    GroundedContext,
    RetrievalCandidate,
)
from english7.modules.tutor.service import TutorService


class FakeRetrieval:
    def __init__(self, context) -> None:
        self.context = context
        self.queries = []

    def retrieve(self, query):
        self.queries.append(query)
        return self.context


class FakeProvider:
    def __init__(self) -> None:
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return AIResponse(
            "Answer from SGK", request.language, (request.evidence[0].fragment_id,)
        )


class MemoryUploads:
    def __init__(self, record) -> None:
        self.record = record

    def get_for_owner(self, upload_id, owner_id):
        if self.record.id == upload_id and self.record.owner_id == owner_id:
            return self.record
        return None


def upload(status=ImageUploadStatus.READY, text="recognized exercise text"):
    return ImageUploadRecord(
        id=uuid4(),
        owner_id=uuid4(),
        object_key="student-images/image.png",
        checksum="a" * 64,
        media_type="image/png",
        size_bytes=10,
        status=status,
        ocr_text=text,
        ocr_confidence=0.9,
        failure_code=None,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        completed_at=datetime.now(timezone.utc),
    )


def context():
    fragment = RetrievalCandidate(
        uuid4(),
        1,
        "Verified textbook evidence",
        12,
        10,
        0.9,
        True,
        ("English 7", "Unit 1", "Getting Started", "1"),
    )
    return GroundedContext(
        (fragment,), (Citation(fragment.fragment_id, 12, 10),)
    )


def test_ready_owned_upload_augments_query_but_not_evidence() -> None:
    record = upload()
    retrieval = FakeRetrieval(context())
    provider = FakeProvider()
    service = TutorService(
        retrieval,
        provider,
        uploads=MemoryUploads(record),
        maximum_query_characters=4000,
    )

    service.ask(
        "Giải bài này",
        Language.VIETNAMESE,
        user_id=record.owner_id,
        upload_id=record.id,
    )

    assert retrieval.queries == ["Giải bài này\nrecognized exercise text"]
    assert provider.requests[0].evidence[0].text == "Verified textbook evidence"


def test_ready_image_can_supply_query_without_typed_text() -> None:
    record = upload()
    retrieval = FakeRetrieval(context())
    service = TutorService(
        retrieval,
        FakeProvider(),
        uploads=MemoryUploads(record),
        maximum_query_characters=4000,
    )

    service.ask(
        "", Language.ENGLISH, user_id=record.owner_id, upload_id=record.id
    )

    assert retrieval.queries == ["recognized exercise text"]


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (ImageUploadStatus.QUEUED, "image_upload_not_ready"),
        (ImageUploadStatus.PROCESSING, "image_upload_not_ready"),
        (ImageUploadStatus.FAILED, "image_processing_failed"),
    ],
)
def test_rejects_upload_that_is_not_ready(status, code) -> None:
    record = upload(status=status)
    service = TutorService(
        FakeRetrieval(context()),
        FakeProvider(),
        uploads=MemoryUploads(record),
        maximum_query_characters=4000,
    )

    with pytest.raises(ApplicationError) as error:
        service.ask(
            "question",
            Language.ENGLISH,
            user_id=record.owner_id,
            upload_id=record.id,
        )

    assert error.value.code == code


def test_rejects_foreign_upload_without_revealing_owner() -> None:
    record = upload()
    service = TutorService(
        FakeRetrieval(context()),
        FakeProvider(),
        uploads=MemoryUploads(record),
        maximum_query_characters=4000,
    )

    with pytest.raises(ApplicationError) as error:
        service.ask(
            "question",
            Language.ENGLISH,
            user_id=uuid4(),
            upload_id=record.id,
        )

    assert error.value.code == "image_upload_not_found"
