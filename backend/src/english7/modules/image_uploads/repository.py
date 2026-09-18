from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from english7.db.models import StudentImageUpload
from english7.modules.image_uploads.domain import ImageUploadRecord, ImageUploadStatus


class SQLAlchemyImageUploadRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _record(upload: StudentImageUpload) -> ImageUploadRecord:
        return ImageUploadRecord(
            id=upload.id,
            owner_id=upload.owner_id,
            object_key=upload.object_key,
            checksum=upload.checksum,
            media_type=upload.media_type,
            size_bytes=upload.size_bytes,
            status=ImageUploadStatus(upload.status),
            ocr_text=upload.ocr_text,
            ocr_confidence=upload.ocr_confidence,
            failure_code=upload.failure_code,
            expires_at=upload.expires_at,
            completed_at=upload.completed_at,
        )

    def create(
        self,
        *,
        owner_id: UUID,
        object_key: str,
        checksum: str,
        media_type: str,
        size_bytes: int,
        expires_at: datetime,
    ) -> ImageUploadRecord:
        with self._session_factory() as session, session.begin():
            upload = StudentImageUpload(
                owner_id=owner_id,
                object_key=object_key,
                checksum=checksum,
                media_type=media_type,
                size_bytes=size_bytes,
                status=ImageUploadStatus.QUEUED.value,
                expires_at=expires_at,
            )
            session.add(upload)
            session.flush()
            return self._record(upload)

    def get_for_owner(
        self, upload_id: UUID, owner_id: UUID
    ) -> ImageUploadRecord | None:
        with self._session_factory() as session:
            upload = session.scalar(
                select(StudentImageUpload).where(
                    StudentImageUpload.id == upload_id,
                    StudentImageUpload.owner_id == owner_id,
                )
            )
            return self._record(upload) if upload else None

    def mark_processing(self, upload_id: UUID) -> None:
        self._update(upload_id, status=ImageUploadStatus.PROCESSING.value)

    def mark_ready(self, upload_id: UUID, text: str, confidence: float) -> None:
        self._update(
            upload_id,
            status=ImageUploadStatus.READY.value,
            ocr_text=text,
            ocr_confidence=confidence,
            failure_code=None,
            completed_at=datetime.now(timezone.utc),
        )

    def mark_failed(self, upload_id: UUID, failure_code: str) -> None:
        self._update(
            upload_id,
            status=ImageUploadStatus.FAILED.value,
            failure_code=failure_code,
            completed_at=datetime.now(timezone.utc),
        )

    def _update(self, upload_id: UUID, **values: object) -> None:
        with self._session_factory() as session, session.begin():
            upload = session.get(StudentImageUpload, upload_id)
            if upload is None:
                raise KeyError(upload_id)
            for key, value in values.items():
                setattr(upload, key, value)
