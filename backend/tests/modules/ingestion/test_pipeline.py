from hashlib import sha256
from uuid import UUID, uuid4

import pytest

from english7.db.models import ReviewStatus
from english7.modules.ingestion.contracts import (
    BoundingBox,
    DetectedRegion,
    OCRResult,
    RenderedPage,
)
from english7.modules.ingestion.pipeline import IngestionCommand, IngestionPipeline


class FakeRenderer:
    def __init__(self, fail: bool = False) -> None:
        self.requested_pages: tuple[int, ...] | None = None
        self.fail = fail

    def render(self, document: bytes, pages: tuple[int, ...]):
        if self.fail:
            raise RuntimeError("/private/path/book.pdf contains a secret")
        self.requested_pages = pages
        return [RenderedPage(page, f"page-{page}".encode(), 1000, 1400) for page in pages]


class FakeDetector:
    version = "layout-test-v1"

    def detect(self, page: RenderedPage):
        return [DetectedRegion("text", BoundingBox(1, 2, 30, 40), 0.91)]


class FakeOCR:
    version = "ocr-test-v1"

    def recognize(self, page: RenderedPage, region: DetectedRegion):
        return OCRResult(f"  Text from {page.pdf_page}  ", 0.88)


class FakeStorage:
    def __init__(self) -> None:
        self.objects: list[tuple[str, bytes, str]] = []

    def put(self, object_key: str, content: bytes, content_type: str) -> None:
        self.objects.append((object_key, content, content_type))


class FakeRepository:
    def __init__(self) -> None:
        self.document = None
        self.fragments = []

    def register_document(self, document):
        self.document = document
        return uuid4()

    def add_fragment(self, fragment):
        self.fragments.append(fragment)
        return uuid4()


class FakeJobs:
    def __init__(self) -> None:
        self.completed: list[UUID] = []
        self.failed: list[tuple[UUID, str]] = []

    def mark_running(self, job_id: UUID) -> None:
        pass

    def mark_completed(self, job_id: UUID) -> None:
        self.completed.append(job_id)

    def mark_failed(self, job_id: UUID, error_code: str) -> None:
        self.failed.append((job_id, error_code))


def build_pipeline(*, renderer=None):
    repository = FakeRepository()
    jobs = FakeJobs()
    pipeline = IngestionPipeline(
        renderer=renderer or FakeRenderer(),
        detector=FakeDetector(),
        ocr=FakeOCR(),
        storage=FakeStorage(),
        repository=repository,
        jobs=jobs,
        ingestion_version="pipeline-test-v1",
        object_prefix="sources",
    )
    return pipeline, repository, jobs


def test_pipeline_registers_hash_and_only_configured_pages_as_drafts() -> None:
    renderer = FakeRenderer()
    pipeline, repository, jobs = build_pipeline(renderer=renderer)
    job_id = uuid4()
    content = b"scanned-pdf"

    result = pipeline.ingest(
        IngestionCommand(
            job_id=job_id,
            filename="English 7.pdf",
            content=content,
            pdf_pages=(12, 13),
            printed_pages={12: 10, 13: 11},
        )
    )

    assert renderer.requested_pages == (12, 13)
    assert repository.document.file_hash == sha256(content).hexdigest()
    assert repository.document.page_count == 2
    assert len(repository.fragments) == 2
    first = repository.fragments[0]
    assert first.pdf_page == 12
    assert first.printed_page == 10
    assert first.bounding_box == BoundingBox(1, 2, 30, 40)
    assert first.detection_confidence == 0.91
    assert first.ocr_confidence == 0.88
    assert first.normalized_text == "Text from 12"
    assert first.review_status is ReviewStatus.DRAFT
    assert result.fragment_count == 2
    assert jobs.completed == [job_id]


def test_pipeline_sanitizes_failure_record() -> None:
    pipeline, _, jobs = build_pipeline(renderer=FakeRenderer(fail=True))
    job_id = uuid4()

    with pytest.raises(RuntimeError):
        pipeline.ingest(
            IngestionCommand(job_id, "book.pdf", b"broken", (1,), {1: 1})
        )

    assert jobs.failed == [(job_id, "ingestion_failed")]
    assert "/private/path" not in jobs.failed[0][1]
