from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Any | None = None
    trace_id: str


class HealthResponse(BaseModel):
    status: str
    service: str

