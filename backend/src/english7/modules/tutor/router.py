from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from english7.api.errors import ApplicationError
from english7.modules.ai.contracts import Language
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.tutor.service import TutorService

router = APIRouter(prefix="/tutor", tags=["tutor"])


class AskTutorRequest(BaseModel):
    question: str = Field(default="", max_length=2000)
    language: Language
    upload_id: UUID | None = None


class CitationResponse(BaseModel):
    fragment_id: UUID
    pdf_page: int
    printed_page: int | None


class TutorResponse(BaseModel):
    answer: str
    language: Language
    citations: tuple[CitationResponse, ...]


def get_tutor_service(request: Request) -> TutorService:
    service = getattr(request.app.state, "tutor_service", None)
    if service is None:
        raise ApplicationError(
            "tutor_unavailable", "Tutor dependencies are not configured", 503
        )
    return service


@router.post("/ask", response_model=TutorResponse)
def ask_tutor(
    payload: AskTutorRequest,
    _user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[TutorService, Depends(get_tutor_service)],
) -> TutorResponse:
    answer = service.ask(
        payload.question,
        payload.language,
        user_id=_user.id,
        upload_id=payload.upload_id,
    )
    return TutorResponse(
        answer=answer.answer,
        language=answer.language,
        citations=tuple(
            CitationResponse(
                fragment_id=item.fragment_id,
                pdf_page=item.pdf_page,
                printed_page=item.printed_page,
            )
            for item in answer.citations
        ),
    )
