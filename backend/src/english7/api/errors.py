from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from english7.api.schemas import ErrorResponse

TRACE_HEADER = "X-Trace-ID"
MAX_TRACE_ID_LENGTH = 128


@dataclass(slots=True)
class ApplicationError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: Any | None = None


def _trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", uuid4().hex)


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    trace_id = _trace_id(request)
    body = ErrorResponse(
        code=code,
        message=message,
        details=details,
        trace_id=trace_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
        headers={TRACE_HEADER: trace_id},
    )


def _http_error_code(status_code: int) -> str:
    if status_code == 404:
        return "not_found"
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    return "http_error"


def install_error_handling(app: FastAPI) -> None:
    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        supplied_trace_id = request.headers.get(TRACE_HEADER, "").strip()
        request.state.trace_id = (
            supplied_trace_id[:MAX_TRACE_ID_LENGTH]
            if supplied_trace_id
            else uuid4().hex
        )
        response = await call_next(request)
        response.headers[TRACE_HEADER] = request.state.trace_id
        return response

    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        request: Request,
        error: ApplicationError,
    ) -> JSONResponse:
        return _response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=error.message,
            details=error.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        return _response(
            request,
            status_code=422,
            code="validation_error",
            message="Request validation failed",
            details=error.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request,
        error: StarletteHTTPException,
    ) -> JSONResponse:
        return _response(
            request,
            status_code=error.status_code,
            code=_http_error_code(error.status_code),
            message=str(error.detail),
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request,
        _error: Exception,
    ) -> JSONResponse:
        return _response(
            request,
            status_code=500,
            code="internal_error",
            message="An unexpected error occurred",
        )

