from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from english7.db.session import get_session_factory
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.textbooks.domain import TextbookFragment, TextbookUnit
from english7.modules.textbooks.repository import SQLAlchemyTextbookRepository
from english7.modules.textbooks.service import TextbookService

router = APIRouter(tags=["textbooks"])


class PaginationResponse(BaseModel):
    offset: int
    limit: int
    count: int


class UnitResponse(BaseModel):
    id: UUID
    number: int
    title: str

    @classmethod
    def from_domain(cls, unit: TextbookUnit) -> "UnitResponse":
        return cls(id=unit.id, number=unit.number, title=unit.title)


class FragmentResponse(BaseModel):
    id: UUID
    unit_id: UUID
    pdf_page: int
    printed_page: int | None
    normalized_text: str
    section_title: str | None = None
    activity_number: str | None = None
    activity_type: str | None = None
    activity_instruction: str | None = None

    @classmethod
    def from_domain(cls, fragment: TextbookFragment) -> "FragmentResponse":
        return cls(
            id=fragment.id,
            unit_id=fragment.unit_id,
            pdf_page=fragment.pdf_page,
            printed_page=fragment.printed_page,
            normalized_text=fragment.normalized_text,
            section_title=fragment.section_title,
            activity_number=fragment.activity_number,
            activity_type=fragment.activity_type,
            activity_instruction=fragment.activity_instruction,
        )


class AudioTrackResponse(BaseModel):
    id: UUID
    track_number: int
    audio_url: str


class ActivityStructureResponse(BaseModel):
    id: UUID
    number: str | None
    activity_type: str
    instruction: str | None
    audio_tracks: list[AudioTrackResponse] = []
    fragments: list[FragmentResponse]


class SectionStructureResponse(BaseModel):
    id: UUID
    title: str
    section_type: str
    position: int
    activities: list[ActivityStructureResponse]


class UnitStructureResponse(BaseModel):
    id: UUID
    number: int
    title: str
    sections: list[SectionStructureResponse]


class UnitListResponse(BaseModel):
    items: list[UnitResponse]
    pagination: PaginationResponse


class FragmentListResponse(BaseModel):
    items: list[FragmentResponse]
    pagination: PaginationResponse


@lru_cache
def get_textbook_service() -> TextbookService:
    return TextbookService(
        SQLAlchemyTextbookRepository(lambda: get_session_factory()())
    )


@router.get("/textbooks/units", response_model=UnitListResponse)
def list_units(
    _user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[TextbookService, Depends(get_textbook_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UnitListResponse:
    units = service.list_units(offset=offset, limit=limit)
    return UnitListResponse(
        items=[UnitResponse.from_domain(unit) for unit in units],
        pagination=PaginationResponse(offset=offset, limit=limit, count=len(units)),
    )


@router.get("/lessons/{unit_id}/structure", response_model=UnitStructureResponse)
def get_unit_structure(
    unit_id: UUID,
    _user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[TextbookService, Depends(get_textbook_service)],
) -> UnitStructureResponse:
    structure = service.get_unit_structure(unit_id)
    return UnitStructureResponse(
        id=structure.id,
        number=structure.number,
        title=structure.title,
        sections=[
            SectionStructureResponse(
                id=sec.id,
                title=sec.title,
                section_type=sec.section_type,
                position=sec.position,
                activities=[
                    ActivityStructureResponse(
                        id=act.id,
                        number=act.number,
                        activity_type=act.activity_type,
                        instruction=act.instruction,
                        audio_tracks=[
                            AudioTrackResponse(
                                id=t.id,
                                track_number=t.track_number,
                                audio_url=t.audio_url,
                            )
                            for t in act.audio_tracks
                        ],
                        fragments=[
                            FragmentResponse.from_domain(frag)
                            for frag in act.fragments
                        ],
                    )
                    for act in sec.activities
                ],
            )
            for sec in structure.sections
        ],
    )


@router.get("/lessons/{unit_id}/fragments", response_model=FragmentListResponse)
def list_fragments(
    unit_id: UUID,
    _user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[TextbookService, Depends(get_textbook_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FragmentListResponse:
    fragments = service.list_fragments(unit_id, offset=offset, limit=limit)
    return FragmentListResponse(
        items=[FragmentResponse.from_domain(fragment) for fragment in fragments],
        pagination=PaginationResponse(
            offset=offset,
            limit=limit,
            count=len(fragments),
        ),
    )

