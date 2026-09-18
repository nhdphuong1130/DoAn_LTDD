from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Protocol
from uuid import UUID, uuid4

from english7.api.errors import ApplicationError
from english7.modules.image_uploads.domain import ImageUploadRecord
from english7.modules.image_uploads.validation import detect_image_format


class ImageUploadRepository(Protocol):
    def create(self, **values) -> ImageUploadRecord: ...

    def get_for_owner(
        self, upload_id: UUID, owner_id: UUID
    ) -> ImageUploadRecord | None: ...


class UploadStorage(Protocol):
    def put(self, object_key: str, content: bytes, content_type: str) -> None: ...


class ImageUploadService:
    def __init__(
        self,
        *,
        repository: ImageUploadRepository,
        storage: UploadStorage,
        maximum_bytes: int,
        allowed_media_types: tuple[str, ...],
        object_prefix: str,
        retention: timedelta,
    ) -> None:
        if maximum_bytes <= 0 or retention <= timedelta(0):
            raise ValueError("Upload size and retention must be positive")
        prefix = object_prefix.strip("/")
        if not prefix or not allowed_media_types:
            raise ValueError("Upload prefix and allowed media types are required")
        self._repository = repository
        self._storage = storage
        self.maximum_bytes = maximum_bytes
        self._allowed = frozenset(allowed_media_types)
        self._prefix = prefix
        self._retention = retention

    def create(
        self,
        owner_id: UUID,
        filename: str,
        claimed_media_type: str,
        content: bytes,
    ) -> ImageUploadRecord:
        del filename
        if len(content) > self.maximum_bytes:
            raise ApplicationError(
                "upload_too_large", "Image exceeds the configured size limit", 413
            )
        image_format = detect_image_format(content)
        if (
            image_format is None
            or image_format.media_type != claimed_media_type
            or image_format.media_type not in self._allowed
        ):
            raise ApplicationError(
                "unsupported_image_type", "Image type is not supported", 415
            )
        upload_id = uuid4()
        object_key = f"{self._prefix}/{owner_id}/{upload_id}.{image_format.extension}"
        self._storage.put(object_key, content, image_format.media_type)
        return self._repository.create(
            owner_id=owner_id,
            object_key=object_key,
            checksum=sha256(content).hexdigest(),
            media_type=image_format.media_type,
            size_bytes=len(content),
            expires_at=datetime.now(timezone.utc) + self._retention,
        )

    def get(self, upload_id: UUID, owner_id: UUID) -> ImageUploadRecord:
        record = self._repository.get_for_owner(upload_id, owner_id)
        if record is None:
            raise ApplicationError(
                "image_upload_not_found", "Image upload was not found", 404
            )
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise ApplicationError(
                "image_upload_expired", "Image upload has expired", 410
            )
        return record
