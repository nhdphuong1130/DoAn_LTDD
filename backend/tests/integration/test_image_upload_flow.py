import os
from datetime import timedelta
from uuid import uuid4

import pytest
from minio import Minio
from sqlalchemy import select

from english7.api.errors import ApplicationError
from english7.db.models import Role, User
from english7.db.session import get_session_factory
from english7.modules.ai.contracts import Language
from english7.modules.image_uploads.domain import ImageUploadStatus
from english7.modules.image_uploads.processor import (
    ImageRegion,
    ImageUploadProcessor,
    RecognizedText,
)
from english7.modules.image_uploads.repository import SQLAlchemyImageUploadRepository
from english7.modules.image_uploads.service import ImageUploadService
from english7.modules.media.storage import MinioUploadStorage
from english7.modules.retrieval.service import GroundedContext
from english7.modules.tutor.service import TutorService


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"integration-exercise"


class EmptyRetrieval:
    def __init__(self) -> None:
        self.queries = []

    def retrieve(self, query):
        self.queries.append(query)
        return GroundedContext((), ())


class ForbiddenProvider:
    def generate(self, _request):
        pytest.fail("OpenRouter must not run without verified SGK evidence")


@pytest.mark.integration
def test_sql_minio_worker_and_closed_world_tutor_flow() -> None:
    endpoint = os.getenv("MINIO_TEST_ENDPOINT")
    access_key = os.getenv("MINIO_TEST_ACCESS_KEY")
    secret_key = os.getenv("MINIO_TEST_SECRET_KEY")
    bucket = os.getenv("MINIO_TEST_BUCKET")
    if not all((endpoint, access_key, secret_key, bucket)):
        pytest.skip("MinIO integration environment is not configured")
    sessions = get_session_factory()
    owner_id = uuid4()
    with sessions() as session, session.begin():
        role_id = session.scalar(select(Role.id).where(Role.name == "student"))
        assert role_id is not None
        session.add(
            User(
                id=owner_id,
                email=f"image-{owner_id}@example.com",
                password_hash="unused",
                role_id=role_id,
            )
        )
    secure = endpoint.startswith("https://")
    endpoint = endpoint.removeprefix("https://").removeprefix("http://")
    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    storage = MinioUploadStorage(client, bucket=bucket)
    repository = SQLAlchemyImageUploadRepository(lambda: sessions())
    service = ImageUploadService(
        repository=repository,
        storage=storage,
        maximum_bytes=1024,
        allowed_media_types=("image/png",),
        object_prefix="integration-images",
        retention=timedelta(minutes=10),
    )
    created = service.create(owner_id, "exercise.png", "image/png", PNG_BYTES)

    assert client.stat_object(bucket, created.object_key).size == len(PNG_BYTES)
    processor = ImageUploadProcessor(
        repository=repository,
        storage=storage,
        detector=lambda _: [ImageRegion(0, 0, 10, 10, "text", 0.9)],
        recognizer=lambda *_: RecognizedText("What is a healthy habit?", 0.95),
        minimum_confidence=0.6,
    )
    for _ in range(20):
        processor.process_next()
        ready = repository.get_for_owner(created.id, owner_id)
        if ready is not None and ready.status is ImageUploadStatus.READY:
            break
    else:
        pytest.fail("The created upload was not processed")

    retrieval = EmptyRetrieval()
    tutor = TutorService(
        retrieval,
        ForbiddenProvider(),
        uploads=repository,
        maximum_query_characters=4000,
    )
    with pytest.raises(ApplicationError) as error:
        tutor.ask(
            "",
            Language.ENGLISH,
            user_id=owner_id,
            upload_id=created.id,
        )

    assert error.value.code == "out_of_scope"
    assert retrieval.queries == ["What is a healthy habit?"]
