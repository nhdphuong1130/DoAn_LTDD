from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from english7.db.models import ReviewStatus


@dataclass(frozen=True, slots=True)
class FragmentForIndexing:
    fragment_id: UUID
    textbook_id: UUID
    textbook_title: str
    unit_id: UUID
    unit_number: int
    unit_title: str
    section_id: UUID
    section_title: str
    activity_id: UUID
    normalized_text: str
    pdf_page: int
    printed_page: int | None
    review_status: ReviewStatus


@dataclass(frozen=True, slots=True)
class IndexedFragment:
    fragment_id: UUID
    textbook_id: UUID
    unit_id: UUID
    section_id: UUID
    activity_id: UUID
    unit_number: int
    text: str
    pdf_page: int
    printed_page: int | None
    embedding: list[float]
    hierarchy: tuple[str, str, str, str]


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class KnowledgeGraphRepository(Protocol):
    def upsert_fragment(self, fragment: IndexedFragment) -> None: ...
