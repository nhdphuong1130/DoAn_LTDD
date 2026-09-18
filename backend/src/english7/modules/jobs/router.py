from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from english7.db.session import get_session_factory
from english7.modules.auth.domain import AuthUser
from english7.modules.auth.router import get_current_user
from english7.modules.auth.service import AuthService
from english7.modules.jobs.domain import JobStatus
from english7.modules.jobs.service import JobService, SQLAlchemyJobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobResponse(BaseModel):
    id: UUID
    job_type: str
    status: JobStatus
    error_code: str | None


@lru_cache
def get_job_service() -> JobService:
    return JobService(SQLAlchemyJobRepository(lambda: get_session_factory()()))


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    user: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobResponse:
    AuthService.authorize(user, {"admin"})
    job = service.get(job_id)
    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        error_code=job.error_code,
    )
