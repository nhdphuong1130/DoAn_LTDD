from dataclasses import dataclass, replace
from uuid import UUID

from english7.db.models import ReviewStatus


@dataclass(frozen=True, slots=True)
class TextbookUnit:
    id: UUID
    number: int
    title: str
    is_published: bool


@dataclass(frozen=True, slots=True)
class TextbookFragment:
    id: UUID
    unit_id: UUID
    pdf_page: int
    printed_page: int | None
    normalized_text: str
    review_status: ReviewStatus
    is_published: bool
    reviewer_id: UUID | None = None

    def verified(self, *, corrected_text: str, reviewer_id: UUID) -> "TextbookFragment":
        return replace(
            self,
            normalized_text=corrected_text.strip(),
            review_status=ReviewStatus.VERIFIED,
            is_published=True,
            reviewer_id=reviewer_id,
        )

