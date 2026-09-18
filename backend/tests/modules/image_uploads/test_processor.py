from datetime import datetime, timedelta, timezone
from uuid import uuid4

from english7.modules.image_uploads.domain import ImageUploadRecord, ImageUploadStatus
from english7.modules.image_uploads.processor import (
    ImageRegion,
    ImageUploadProcessor,
    RecognizedText,
)


class MemoryRepository:
    def __init__(self, record) -> None:
        self.record = record
        self.ready = None
        self.failure = None

    def claim_next(self):
        return self.record

    def mark_ready(self, upload_id, text, confidence):
        self.ready = (upload_id, text, confidence)

    def mark_failed(self, upload_id, failure_code):
        self.failure = (upload_id, failure_code)


class MemoryStorage:
    def get(self, object_key):
        assert object_key == "student-images/image.png"
        return b"image-bytes"


def upload_record():
    return ImageUploadRecord(
        id=uuid4(),
        owner_id=uuid4(),
        object_key="student-images/image.png",
        checksum="a" * 64,
        media_type="image/png",
        size_bytes=10,
        status=ImageUploadStatus.PROCESSING,
        ocr_text=None,
        ocr_confidence=None,
        failure_code=None,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        completed_at=None,
    )


def test_orders_regions_filters_confidence_and_normalizes_text() -> None:
    record = upload_record()
    repository = MemoryRepository(record)
    regions = [
        ImageRegion(0, 100, 50, 20, "text", 0.9),
        ImageRegion(10, 10, 50, 20, "text", 0.8),
        ImageRegion(5, 50, 50, 20, "text", 0.7),
    ]
    recognized = {
        10: RecognizedText("  First   line ", 0.95),
        50: RecognizedText("ignore me", 0.40),
        100: RecognizedText("Second line", 0.85),
    }
    processor = ImageUploadProcessor(
        repository=repository,
        storage=MemoryStorage(),
        detector=lambda _: regions,
        recognizer=lambda _, region: recognized[region.y],
        minimum_confidence=0.60,
    )

    assert processor.process_next() is True
    assert repository.ready == (record.id, "First line\nSecond line", 0.90)
    assert repository.failure is None


def test_marks_no_usable_text_with_stable_failure() -> None:
    record = upload_record()
    repository = MemoryRepository(record)
    processor = ImageUploadProcessor(
        repository=repository,
        storage=MemoryStorage(),
        detector=lambda _: [ImageRegion(0, 0, 10, 10, "text", 0.9)],
        recognizer=lambda *_: RecognizedText("", 0.99),
        minimum_confidence=0.60,
    )

    assert processor.process_next() is True
    assert repository.failure == (record.id, "image_text_not_found")


def test_marks_provider_exception_without_leaking_details() -> None:
    record = upload_record()
    repository = MemoryRepository(record)

    def broken_detector(_):
        raise RuntimeError("provider credentials or model path")

    processor = ImageUploadProcessor(
        repository=repository,
        storage=MemoryStorage(),
        detector=broken_detector,
        recognizer=lambda *_: RecognizedText("unused", 1.0),
        minimum_confidence=0.60,
    )

    assert processor.process_next() is True
    assert repository.failure == (record.id, "image_processing_failed")


def test_returns_false_when_queue_is_empty() -> None:
    repository = MemoryRepository(None)
    processor = ImageUploadProcessor(
        repository=repository,
        storage=MemoryStorage(),
        detector=lambda _: [],
        recognizer=lambda *_: RecognizedText("unused", 1.0),
        minimum_confidence=0.60,
    )

    assert processor.process_next() is False
