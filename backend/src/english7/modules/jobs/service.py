from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from english7.api.errors import ApplicationError
from english7.db.models import Job
from english7.modules.jobs.domain import JobRecord, JobStatus


class JobRepository(Protocol):
    def get(self, job_id: UUID) -> JobRecord | None: ...

    def set_status(
        self, job_id: UUID, status: JobStatus, error_code: str | None = None
    ) -> None: ...


class SQLAlchemyJobRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _record(job: Job) -> JobRecord:
        return JobRecord(job.id, job.job_type, JobStatus(job.status), job.error_code)

    def get(self, job_id: UUID) -> JobRecord | None:
        with self._session_factory() as session:
            job = session.scalar(select(Job).where(Job.id == job_id))
            return self._record(job) if job else None

    def set_status(
        self, job_id: UUID, status: JobStatus, error_code: str | None = None
    ) -> None:
        with self._session_factory() as session, session.begin():
            job = session.scalar(select(Job).where(Job.id == job_id))
            if job is None:
                raise KeyError(job_id)
            job.status = status.value
            job.error_code = error_code


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def get(self, job_id: UUID) -> JobRecord:
        job = self._repository.get(job_id)
        if job is None:
            raise ApplicationError("job_not_found", "Job was not found", 404)
        return job

    def mark_running(self, job_id: UUID) -> None:
        self._repository.set_status(job_id, JobStatus.RUNNING)

    def mark_completed(self, job_id: UUID) -> None:
        self._repository.set_status(job_id, JobStatus.COMPLETED)

    def mark_failed(self, job_id: UUID, error_code: str) -> None:
        self._repository.set_status(job_id, JobStatus.FAILED, error_code)
