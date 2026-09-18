from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from english7.api.errors import ApplicationError
from english7.modules.image_uploads.domain import ImageUploadRecord, ImageUploadStatus
from english7.modules.image_uploads.service import ImageUploadService


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"exercise-image"


class MemoryRepository:
    def __init__(self) -> None:
        self.records: dict = {}

    def create(self, **values):
        record = ImageUploadRecord(
            id=uuid4(),
            status=ImageUploadStatus.QUEUED,
            ocr_text=None,
            ocr_confidence=None,
            failure_code=None,
            completed_at=None,
            **values,
        )
        self.records[record.id] = record
        return record

    def get_for_owner(self, upload_id, owner_id):
        record = self.records.get(upload_id)
        return record if record and record.owner_id == owner_id else None


class MemoryStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, str]] = []

    def put(self, object_key, content, content_type):
        self.uploads.append((object_key, content, content_type))


def make_service(max_bytes: int = 1024):
    repository = MemoryRepository()
    storage = MemoryStorage()
    service = ImageUploadService(
        repository=repository,
        storage=storage,
        maximum_bytes=max_bytes,
        allowed_media_types=("image/jpeg", "image/png", "image/webp"),
        object_prefix="student-images",
        retention=timedelta(minutes=60),
    )
    return service, repository, storage


def test_validates_signature_and_generates_storage_key() -> None:
    service, _, storage = make_service()
    owner_id = uuid4()

    created = service.create(
        owner_id=owner_id,
        filename="../../exercise.png",
        claimed_media_type="image/png",
        content=PNG_BYTES,
    )

    assert created.owner_id == owner_id
    assert created.media_type == "image/png"
    assert created.object_key.startswith("student-images/")
    assert "exercise.png" not in created.object_key
    assert storage.uploads == [(created.object_key, PNG_BYTES, "image/png")]


@pytest.mark.parametrize(
    ("claimed_type", "content", "code"),
    [
        ("image/png", b"not-an-image", "unsupported_image_type"),
        ("image/jpeg", PNG_BYTES, "unsupported_image_type"),
    ],
)
def test_rejects_invalid_or_spoofed_image(claimed_type, content, code) -> None:
    service, _, _ = make_service()

    with pytest.raises(ApplicationError) as error:
        service.create(uuid4(), "image.png", claimed_type, content)

    assert error.value.code == code


def test_rejects_content_over_configured_limit() -> None:
    service, _, _ = make_service(max_bytes=len(PNG_BYTES) - 1)

    with pytest.raises(ApplicationError) as error:
        service.create(uuid4(), "image.png", "image/png", PNG_BYTES)

    assert error.value.code == "upload_too_large"


def test_owner_cannot_read_another_students_upload() -> None:
    service, _, _ = make_service()
    created = service.create(uuid4(), "image.png", "image/png", PNG_BYTES)

    with pytest.raises(ApplicationError) as error:
        service.get(created.id, uuid4())

    assert error.value.code == "image_upload_not_found"


def test_expired_upload_is_not_returned_as_usable() -> None:
    service, repository, _ = make_service()
    owner_id = uuid4()
    upload_id = uuid4()
    repository.records[upload_id] = ImageUploadRecord(
        id=upload_id,
        owner_id=owner_id,
        object_key="student-images/id.png",
        checksum="a" * 64,
        media_type="image/png",
        size_bytes=10,
        status=ImageUploadStatus.READY,
        ocr_text="question",
        ocr_confidence=0.9,
        failure_code=None,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        completed_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ApplicationError) as error:
        service.get(upload_id, owner_id)

    assert error.value.code == "image_upload_expired"
