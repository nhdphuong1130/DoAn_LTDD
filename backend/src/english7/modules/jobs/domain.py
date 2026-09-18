from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class JobRecord:
    id: UUID
    job_type: str
    status: JobStatus
    error_code: str | None
