from datetime import datetime, timedelta, timezone
from uuid import uuid4

from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.image_uploads.domain import ImageUploadRecord, ImageUploadStatus
from english7.modules.image_uploads.router import get_image_upload_service


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"exercise-image"


class FakeImageUploadService:
    def __init__(self, owner_id) -> None:
        self.maximum_bytes = 1024
        self.owner_id = owner_id
        self.calls = []
        self.record = ImageUploadRecord(
            id=uuid4(),
            owner_id=owner_id,
            object_key="student-images/generated.png",
            checksum="a" * 64,
            media_type="image/png",
            size_bytes=len(PNG_BYTES),
            status=ImageUploadStatus.QUEUED,
            ocr_text=None,
            ocr_confidence=None,
            failure_code=None,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
            completed_at=None,
        )

    def create(self, owner_id, filename, claimed_media_type, content):
        self.calls.append((owner_id, filename, claimed_media_type, content))
        return self.record

    def get(self, upload_id, owner_id):
        assert upload_id == self.record.id
        assert owner_id == self.owner_id
        return self.record


def test_student_uploads_image_and_reads_owner_scoped_status(client) -> None:
    student = AuthUser.new(
        email="student@example.com", password_hash="unused", role="student"
    )
    service = FakeImageUploadService(student.id)
    app.dependency_overrides[get_current_user] = lambda: student
    app.dependency_overrides[get_image_upload_service] = lambda: service
    try:
        uploaded = client.post(
            "/api/v1/tutor/images",
            files={"image": ("exercise.png", PNG_BYTES, "image/png")},
        )
        status = client.get(
            f"/api/v1/tutor/images/{service.record.id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert uploaded.status_code == 202
    assert uploaded.json()["id"] == str(service.record.id)
    assert uploaded.json()["status"] == "queued"
    assert "object_key" not in uploaded.json()
    assert status.status_code == 200
    assert status.json()["status"] == "queued"
    assert service.calls == [
        (student.id, "exercise.png", "image/png", PNG_BYTES)
    ]
