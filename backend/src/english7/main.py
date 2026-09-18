from fastapi import FastAPI

from english7.api.errors import install_error_handling
from english7.api.router import router
from english7.core.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.service_name)
install_error_handling(app)
app.include_router(router, prefix=settings.api_prefix)
