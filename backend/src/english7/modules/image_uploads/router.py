from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from pydantic import BaseModel

from english7.api.errors import ApplicationError
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.image_uploads.domain import ImageUploadRecord, ImageUploadStatus
from english7.modules.image_uploads.service import ImageUploadService

router = APIRouter(prefix="/tutor/images", tags=["tutor-images"])


class ImageUploadResponse(BaseModel):
    id: UUID
    status: ImageUploadStatus
    ocr_text: str | None
    ocr_confidence: float | None
    failure_code: str | None
    expires_at: datetime


def get_image_upload_service(request: Request) -> ImageUploadService:
    service = getattr(request.app.state, "image_upload_service", None)
    if service is None:
        raise ApplicationError(
            "image_upload_unavailable", "Image upload service is not configured", 503
        )
    return service


def _response(record: ImageUploadRecord) -> ImageUploadResponse:
    return ImageUploadResponse(
        id=record.id,
        status=record.status,
        ocr_text=record.ocr_text,
        ocr_confidence=record.ocr_confidence,
        failure_code=record.failure_code,
        expires_at=record.expires_at,
    )


@router.post("", response_model=ImageUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_image(
    image: Annotated[UploadFile, File()],
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[ImageUploadService, Depends(get_image_upload_service)],
) -> ImageUploadResponse:
    content = await image.read(service.maximum_bytes + 1)
    record = service.create(
        user.id,
        image.filename or "upload",
        image.content_type or "application/octet-stream",
        content,
    )
    return _response(record)


@router.get("/{upload_id}", response_model=ImageUploadResponse)
def image_status(
    upload_id: UUID,
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[ImageUploadService, Depends(get_image_upload_service)],
) -> ImageUploadResponse:
    return _response(service.get(upload_id, user.id))
