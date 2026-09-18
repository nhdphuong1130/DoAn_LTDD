from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.db.models import ReviewStatus
from english7.modules.media.storage import MinioStorage
from english7.modules.textbooks.domain import TextbookFragment, TextbookUnit
from english7.modules.textbooks.service import TextbookService


class MemoryTextbookRepository:
    def __init__(self) -> None:
        self.units: list[TextbookUnit] = []
        self.fragments: dict = {}
        self.audit_events: list[dict] = []

    def list_published_units(self, offset: int, limit: int):
        published = [unit for unit in self.units if unit.is_published]
        return published[offset : offset + limit]

    def list_published_fragments(self, unit_id, offset: int, limit: int):
        published = [
            fragment
            for fragment in self.fragments.values()
            if fragment.unit_id == unit_id
            and fragment.is_published
            and fragment.review_status == ReviewStatus.VERIFIED
        ]
        return published[offset : offset + limit]

    def get_fragment(self, fragment_id):
        return self.fragments.get(fragment_id)

    def save_fragment(self, fragment):
        self.fragments[fragment.id] = fragment
        return fragment

    def add_audit_event(self, event):
        self.audit_events.append(event)


def test_student_lists_only_published_units_and_verified_fragments() -> None:
    repository = MemoryTextbookRepository()
    published_unit = TextbookUnit(uuid4(), 1, "Hobbies", True)
    draft_unit = TextbookUnit(uuid4(), 2, "Healthy Living", False)
    repository.units.extend([published_unit, draft_unit])
    verified = TextbookFragment(
        id=uuid4(),
        unit_id=published_unit.id,
        pdf_page=10,
        printed_page=8,
        normalized_text="A hobby is an activity you do for pleasure.",
        review_status=ReviewStatus.VERIFIED,
        is_published=True,
    )
    draft = TextbookFragment(
        id=uuid4(),
        unit_id=published_unit.id,
        pdf_page=10,
        printed_page=8,
        normalized_text="Unverified OCR output",
        review_status=ReviewStatus.DRAFT,
        is_published=False,
    )
    repository.fragments = {verified.id: verified, draft.id: draft}
    service = TextbookService(repository)

    assert service.list_units(offset=0, limit=20) == [published_unit]
    assert service.list_fragments(published_unit.id, offset=0, limit=20) == [verified]


def test_admin_corrects_and_verifies_fragment_with_audit_event() -> None:
    repository = MemoryTextbookRepository()
    fragment = TextbookFragment(
        id=uuid4(),
        unit_id=uuid4(),
        pdf_page=10,
        printed_page=8,
        normalized_text="Hobies are fun.",
        review_status=ReviewStatus.DRAFT,
        is_published=False,
    )
    repository.fragments[fragment.id] = fragment
    reviewer_id = uuid4()
    service = TextbookService(repository)

    updated = service.verify_fragment(
        fragment.id,
        corrected_text="Hobbies are fun.",
        reviewer_id=reviewer_id,
    )

    assert updated.normalized_text == "Hobbies are fun."
    assert updated.review_status == ReviewStatus.VERIFIED
    assert updated.is_published is True
    assert updated.reviewer_id == reviewer_id
    assert repository.audit_events[0]["action"] == "source_fragment.verified"


def test_missing_fragment_cannot_be_verified() -> None:
    service = TextbookService(MemoryTextbookRepository())

    with pytest.raises(ApplicationError) as error:
        service.verify_fragment(
            uuid4(),
            corrected_text="Correct text",
            reviewer_id=uuid4(),
        )

    assert error.value.code == "fragment_not_found"


class FakeMinioClient:
    def presigned_get_object(self, bucket_name, object_name, expires):
        assert bucket_name == "media"
        assert object_name == "audio/001.mp3"
        return "https://storage.example/media/audio/001.mp3?signature=signed"


def test_media_url_is_generated_without_exposing_credentials() -> None:
    storage = MinioStorage(FakeMinioClient(), bucket="media", expiry_seconds=300)

    url = storage.presigned_download("audio/001.mp3")

    assert "username" not in url
    assert "password" not in url
    assert "signature=signed" in url

