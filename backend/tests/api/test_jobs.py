from uuid import uuid4

from english7.main import app
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.jobs.domain import JobRecord, JobStatus
from english7.modules.jobs.router import get_job_service


class FakeJobService:
    def __init__(self, record: JobRecord) -> None:
        self.record = record

    def get(self, job_id):
        assert job_id == self.record.id
        return self.record


def test_admin_can_read_job_status(client) -> None:
    record = JobRecord(uuid4(), "textbook_ingestion", JobStatus.RUNNING, None)
    admin = AuthUser.new(
        email="admin@example.com", password_hash="unused", role="admin"
    )
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_job_service] = lambda: FakeJobService(record)
    try:
        response = client.get(f"/api/v1/jobs/{record.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": str(record.id),
        "job_type": "textbook_ingestion",
        "status": "running",
        "error_code": None,
    }


def test_student_cannot_read_ingestion_job(client) -> None:
    record = JobRecord(uuid4(), "textbook_ingestion", JobStatus.PENDING, None)
    student = AuthUser.new(
        email="student@example.com", password_hash="unused", role="student"
    )
    app.dependency_overrides[get_current_user] = lambda: student
    app.dependency_overrides[get_job_service] = lambda: FakeJobService(record)
    try:
        response = client.get(f"/api/v1/jobs/{record.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
