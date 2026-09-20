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
    section_id: UUID | None = None
    section_title: str | None = None
    activity_id: UUID | None = None
    activity_number: str | None = None
    activity_type: str | None = None
    activity_instruction: str | None = None

    def verified(self, *, corrected_text: str, reviewer_id: UUID) -> "TextbookFragment":
        return replace(
            self,
            normalized_text=corrected_text.strip(),
            review_status=ReviewStatus.VERIFIED,
            is_published=True,
            reviewer_id=reviewer_id,
        )


@dataclass(frozen=True, slots=True)
class TextbookAudioTrack:
    id: UUID
    track_number: int
    audio_url: str


@dataclass(frozen=True, slots=True)
class TextbookActivityDetail:
    id: UUID
    section_id: UUID
    number: str | None
    activity_type: str
    instruction: str | None
    fragments: list[TextbookFragment]
    audio_tracks: list[TextbookAudioTrack] = ()


@dataclass(frozen=True, slots=True)
class TextbookSectionDetail:
    id: UUID
    unit_id: UUID
    title: str
    section_type: str
    position: int
    activities: list[TextbookActivityDetail]


@dataclass(frozen=True, slots=True)
class TextbookUnitStructure:
    id: UUID
    number: int
    title: str
    is_published: bool
    sections: list[TextbookSectionDetail]

