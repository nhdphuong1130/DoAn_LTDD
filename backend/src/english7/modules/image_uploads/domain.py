from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ImageUploadStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ImageUploadRecord:
    id: UUID
    owner_id: UUID
    object_key: str
    checksum: str
    media_type: str
    size_bytes: int
    status: ImageUploadStatus
    ocr_text: str | None
    ocr_confidence: float | None
    failure_code: str | None
    expires_at: datetime
    completed_at: datetime | None
