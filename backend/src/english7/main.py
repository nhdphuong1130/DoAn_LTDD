from contextlib import asynccontextmanager

from fastapi import FastAPI

from english7.api.errors import install_error_handling
from english7.api.router import router
from english7.bootstrap import configure_runtime
from english7.core.settings import get_settings
from english7.modules.speaking.upload_limit import SpeakingUploadLimit

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    runtime = configure_runtime(application, settings)
    try:
        yield
    finally:
        if runtime is not None:
            runtime.close()


app = FastAPI(title=settings.service_name, lifespan=lifespan)
app.add_middleware(SpeakingUploadLimit, api_prefix=settings.api_prefix)
install_error_handling(app)
app.include_router(router, prefix=settings.api_prefix)
