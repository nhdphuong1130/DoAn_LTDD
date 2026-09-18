from fastapi import APIRouter

from english7.api.schemas import HealthResponse
from english7.core.settings import get_settings
from english7.modules.auth.router import router as auth_router

router = APIRouter()
router.include_router(auth_router)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.service_name)
