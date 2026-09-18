from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from english7.api.errors import ApplicationError
from english7.modules.ai.contracts import AIProvider, AIRequest, Evidence, Language
from english7.modules.image_uploads.domain import ImageUploadRecord, ImageUploadStatus
from english7.modules.retrieval.service import Citation, RetrievalRepository


@dataclass(frozen=True, slots=True)
class TutorAnswer:
    answer: str
    language: Language
    citations: tuple[Citation, ...]


class ContextRetriever(RetrievalRepository):
    def retrieve(self, query: str): ...


class TutorUploadRepository(Protocol):
    def get_for_owner(
        self, upload_id: UUID, owner_id: UUID
    ) -> ImageUploadRecord | None: ...


class TutorService:
    def __init__(
        self,
        retrieval,
        provider: AIProvider,
        *,
        uploads: TutorUploadRepository | None = None,
        maximum_query_characters: int = 4000,
    ) -> None:
        if maximum_query_characters <= 0:
            raise ValueError("Maximum query characters must be positive")
        self._retrieval = retrieval
        self._provider = provider
        self._uploads = uploads
        self._maximum_query_characters = maximum_query_characters

    def ask(
        self,
        question: str,
        language: Language,
        *,
        user_id: UUID | None = None,
        upload_id: UUID | None = None,
    ) -> TutorAnswer:
        parts = [" ".join(question.split())] if question.strip() else []
        if upload_id is not None:
            if self._uploads is None or user_id is None:
                raise ApplicationError(
                    "image_upload_unavailable",
                    "Image upload support is not configured",
                    503,
                )
            upload = self._uploads.get_for_owner(upload_id, user_id)
            if upload is None:
                raise ApplicationError(
                    "image_upload_not_found", "Image upload was not found", 404
                )
            expires_at = upload.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise ApplicationError(
                    "image_upload_expired", "Image upload has expired", 410
                )
            if upload.status in {
                ImageUploadStatus.QUEUED,
                ImageUploadStatus.PROCESSING,
            }:
                raise ApplicationError(
                    "image_upload_not_ready", "Image is still being processed", 409
                )
            if upload.status is ImageUploadStatus.FAILED:
                code = upload.failure_code or "image_processing_failed"
                raise ApplicationError(code, "Image processing failed", 422)
            if not upload.ocr_text or not upload.ocr_text.strip():
                raise ApplicationError(
                    "image_text_not_found", "No usable text was found in the image", 422
                )
            parts.append(" ".join(upload.ocr_text.split()))
        query = "\n".join(parts)[: self._maximum_query_characters]
        if not query:
            raise ApplicationError("question_required", "A question is required", 422)
        context = self._retrieval.retrieve(query)
        if not context.fragments:
            raise ApplicationError(
                "out_of_scope",
                "No verified textbook evidence was found for this question",
                422,
            )
        evidence = tuple(
            Evidence(
                item.fragment_id,
                item.text,
                item.pdf_page,
                item.printed_page,
            )
            for item in context.fragments
        )
        generated = self._provider.generate(AIRequest(query, language, evidence))
        if generated.language != language or not generated.answer:
            raise ApplicationError(
                "invalid_ai_response", "AI response validation failed", 502
            )
        allowed = {item.fragment_id for item in evidence}
        if not generated.citations or not set(generated.citations).issubset(allowed):
            raise ApplicationError(
                "invalid_ai_citations", "AI citations failed source validation", 502
            )
        citations_by_id = {
            citation.fragment_id: citation for citation in context.citations
        }
        try:
            citations = tuple(
                citations_by_id[fragment_id] for fragment_id in generated.citations
            )
        except KeyError:
            raise ApplicationError(
                "invalid_ai_citations", "AI citations failed source validation", 502
            ) from None
        return TutorAnswer(generated.answer, generated.language, citations)
