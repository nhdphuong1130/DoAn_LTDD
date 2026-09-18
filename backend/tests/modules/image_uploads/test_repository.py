from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from english7.db.base import Base
from english7.modules.image_uploads.domain import ImageUploadStatus
from english7.modules.image_uploads.repository import SQLAlchemyImageUploadRepository


def test_repository_scopes_uploads_to_owner_and_persists_ready_result() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = SQLAlchemyImageUploadRepository(sessions)
    owner_id = uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    created = repository.create(
        owner_id=owner_id,
        object_key=f"student-images/{uuid4()}.png",
        checksum="a" * 64,
        media_type="image/png",
        size_bytes=123,
        expires_at=expires_at,
    )

    assert created.status is ImageUploadStatus.QUEUED
    assert repository.get_for_owner(created.id, uuid4()) is None

    repository.mark_processing(created.id)
    assert (
        repository.get_for_owner(created.id, owner_id).status
        is ImageUploadStatus.PROCESSING
    )

    repository.mark_ready(created.id, "recognized question", 0.91)
    ready = repository.get_for_owner(created.id, owner_id)
    assert ready is not None
    assert ready.status is ImageUploadStatus.READY
    assert ready.ocr_text == "recognized question"
    assert ready.ocr_confidence == 0.91
    assert ready.completed_at is not None


def test_repository_persists_stable_processing_failure_code() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    repository = SQLAlchemyImageUploadRepository(sessions)
    owner_id = uuid4()
    created = repository.create(
        owner_id=owner_id,
        object_key=f"student-images/{uuid4()}.webp",
        checksum="b" * 64,
        media_type="image/webp",
        size_bytes=321,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    repository.mark_failed(created.id, "image_text_not_found")

    failed = repository.get_for_owner(created.id, owner_id)
    assert failed is not None
    assert failed.status is ImageUploadStatus.FAILED
    assert failed.failure_code == "image_text_not_found"
    assert failed.completed_at is not None
