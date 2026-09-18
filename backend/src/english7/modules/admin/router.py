from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from english7.db.models import ReviewStatus
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.auth.service import AuthService
from english7.modules.textbooks.router import get_textbook_service
from english7.modules.textbooks.service import TextbookService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_textbook_service() -> TextbookService:
    return get_textbook_service()


class VerifyFragmentRequest(BaseModel):
    normalized_text: str = Field(min_length=1)


class AdminFragmentResponse(BaseModel):
    id: UUID
    normalized_text: str
    review_status: ReviewStatus
    is_published: bool
    reviewer_id: UUID | None


@router.patch(
    "/fragments/{fragment_id}/verify",
    response_model=AdminFragmentResponse,
)
def verify_fragment(
    fragment_id: UUID,
    payload: VerifyFragmentRequest,
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[TextbookService, Depends(get_admin_textbook_service)],
) -> AdminFragmentResponse:
    AuthService.authorize(user, {"admin"})
    fragment = service.verify_fragment(
        fragment_id,
        corrected_text=payload.normalized_text,
        reviewer_id=user.id,
    )
    return AdminFragmentResponse(
        id=fragment.id,
        normalized_text=fragment.normalized_text,
        review_status=fragment.review_status,
        is_published=fragment.is_published,
        reviewer_id=fragment.reviewer_id,
    )

