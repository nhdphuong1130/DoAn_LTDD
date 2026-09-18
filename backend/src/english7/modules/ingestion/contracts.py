from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from english7.db.models import ReviewStatus


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class RenderedPage:
    pdf_page: int
    image: bytes
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class DetectedRegion:
    region_type: str
    bounding_box: BoundingBox
    confidence: float


@dataclass(frozen=True, slots=True)
class OCRResult:
    text: str
    confidence: float


@dataclass(frozen=True, slots=True)
class SourceDocumentDraft:
    filename: str
    file_hash: str
    page_count: int
    ingestion_version: str
    object_key: str


@dataclass(frozen=True, slots=True)
class SourceFragmentDraft:
    source_document_id: UUID
    pdf_page: int
    printed_page: int | None
    region_type: str
    bounding_box: BoundingBox
    ocr_text: str
    normalized_text: str
    detection_confidence: float
    ocr_confidence: float
    detector_version: str
    ocr_version: str
    review_status: ReviewStatus = ReviewStatus.DRAFT


class PageRenderer(Protocol):
    def render(
        self, document: bytes, pages: tuple[int, ...]
    ) -> list[RenderedPage]: ...


class LayoutDetector(Protocol):
    version: str

    def detect(self, page: RenderedPage) -> list[DetectedRegion]: ...


class OCREngine(Protocol):
    version: str

    def recognize(
        self, page: RenderedPage, region: DetectedRegion
    ) -> OCRResult: ...


class ObjectStorage(Protocol):
    def put(self, object_key: str, content: bytes, content_type: str) -> None: ...


class IngestionRepository(Protocol):
    def register_document(self, document: SourceDocumentDraft) -> UUID: ...

    def add_fragment(self, fragment: SourceFragmentDraft) -> UUID: ...


class JobTracker(Protocol):
    def mark_running(self, job_id: UUID) -> None: ...

    def mark_completed(self, job_id: UUID) -> None: ...

    def mark_failed(self, job_id: UUID, error_code: str) -> None: ...
