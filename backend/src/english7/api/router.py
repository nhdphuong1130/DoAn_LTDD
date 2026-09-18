from fastapi import APIRouter

from english7.api.schemas import HealthResponse
from english7.core.settings import get_settings
from english7.modules.admin.router import router as admin_router
from english7.modules.auth.router import router as auth_router
from english7.modules.jobs.router import router as jobs_router
from english7.modules.image_uploads.router import router as image_uploads_router
from english7.modules.quizzes.router import router as quizzes_router
from english7.modules.textbooks.router import router as textbooks_router
from english7.modules.tutor.router import router as tutor_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(textbooks_router)
router.include_router(admin_router)
router.include_router(jobs_router)
router.include_router(tutor_router)
router.include_router(image_uploads_router)
router.include_router(quizzes_router)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.service_name)
