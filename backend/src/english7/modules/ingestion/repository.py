from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from english7.db.models import SourceDocument, SourceFragment
from english7.modules.ingestion.contracts import (
    SourceDocumentDraft,
    SourceFragmentDraft,
)


class SQLAlchemyIngestionRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def register_document(self, draft: SourceDocumentDraft) -> UUID:
        document = SourceDocument(
            original_filename=draft.filename,
            object_key=draft.object_key,
            file_hash=draft.file_hash,
            page_count=draft.page_count,
            ingestion_version=draft.ingestion_version,
        )
        with self._session_factory() as session, session.begin():
            session.add(document)
            session.flush()
            return document.id

    def add_fragment(self, draft: SourceFragmentDraft) -> UUID:
        box = draft.bounding_box
        fragment = SourceFragment(
            source_document_id=draft.source_document_id,
            pdf_page=draft.pdf_page,
            printed_page=draft.printed_page,
            region_type=draft.region_type,
            x=box.x,
            y=box.y,
            width=box.width,
            height=box.height,
            ocr_text=draft.ocr_text,
            normalized_text=draft.normalized_text,
            detection_confidence=draft.detection_confidence,
            ocr_confidence=draft.ocr_confidence,
            detector_version=draft.detector_version,
            ocr_version=draft.ocr_version,
            review_status=draft.review_status.value,
            is_published=False,
        )
        with self._session_factory() as session, session.begin():
            session.add(fragment)
            session.flush()
            return fragment.id
