from fastapi import APIRouter

from english7.api.schemas import HealthResponse
from english7.core.settings import get_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.service_name)

