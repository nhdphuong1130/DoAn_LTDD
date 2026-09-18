from fastapi import FastAPI

from english7.core.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.service_name)


@app.get(f"{settings.api_prefix}/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}

