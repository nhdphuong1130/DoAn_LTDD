from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePath
from uuid import UUID

from english7.modules.ingestion.contracts import (
    IngestionRepository,
    JobTracker,
    LayoutDetector,
    OCREngine,
    ObjectStorage,
    PageRenderer,
    SourceDocumentDraft,
    SourceFragmentDraft,
)


@dataclass(frozen=True, slots=True)
class IngestionCommand:
    job_id: UUID
    filename: str
    content: bytes
    pdf_pages: tuple[int, ...]
    printed_pages: dict[int, int]


@dataclass(frozen=True, slots=True)
class IngestionResult:
    document_id: UUID
    fragment_count: int


class IngestionPipeline:
    def __init__(
        self,
        *,
        renderer: PageRenderer,
        detector: LayoutDetector,
        ocr: OCREngine,
        storage: ObjectStorage,
        repository: IngestionRepository,
        jobs: JobTracker,
        ingestion_version: str,
        object_prefix: str,
    ) -> None:
        self._renderer = renderer
        self._detector = detector
        self._ocr = ocr
        self._storage = storage
        self._repository = repository
        self._jobs = jobs
        self._ingestion_version = ingestion_version
        self._object_prefix = object_prefix.strip("/")

    def ingest(self, command: IngestionCommand) -> IngestionResult:
        self._jobs.mark_running(command.job_id)
        try:
            digest = sha256(command.content).hexdigest()
            safe_name = PurePath(command.filename).name
            object_key = f"{self._object_prefix}/{digest}/{safe_name}"
            self._storage.put(object_key, command.content, "application/pdf")
            pages = self._renderer.render(command.content, command.pdf_pages)
            document_id = self._repository.register_document(
                SourceDocumentDraft(
                    safe_name,
                    digest,
                    len(pages),
                    self._ingestion_version,
                    object_key,
                )
            )
            fragment_count = 0
            for page in pages:
                for region in self._detector.detect(page):
                    recognized = self._ocr.recognize(page, region)
                    normalized = " ".join(recognized.text.split())
                    if not normalized:
                        continue
                    self._repository.add_fragment(
                        SourceFragmentDraft(
                            source_document_id=document_id,
                            pdf_page=page.pdf_page,
                            printed_page=command.printed_pages.get(page.pdf_page),
                            region_type=region.region_type,
                            bounding_box=region.bounding_box,
                            ocr_text=recognized.text,
                            normalized_text=normalized,
                            detection_confidence=region.confidence,
                            ocr_confidence=recognized.confidence,
                            detector_version=self._detector.version,
                            ocr_version=self._ocr.version,
                        )
                    )
                    fragment_count += 1
            self._jobs.mark_completed(command.job_id)
            return IngestionResult(document_id, fragment_count)
        except Exception:
            self._jobs.mark_failed(command.job_id, "ingestion_failed")
            raise
