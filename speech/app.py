"""Private, optional CPU speech service. Start with one uvicorn worker."""
import asyncio
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_UPLOAD = 2 * 1024 * 1024
INFERENCE_TIMEOUT = 120
logger = logging.getLogger(__name__)


class Synthesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=400)
    voice_id: str = Field(min_length=1, max_length=80)

    @field_validator("text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Text is empty")
        return value.strip()


class BodyLimit:
    """Cap streamed bodies before Starlette can spool multipart data to disk."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        limit = MAX_UPLOAD + 65536 if scope["path"] == "/transcribe" else 8192
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > limit:
                return await JSONResponse({"detail": "Request too large"}, 413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, bounded_receive, send)


def create_app(engine=None):
    state = {"engine": engine}
    lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        if state["engine"] is None:
            try:
                from speech.engine import LocalEngine
                state["engine"] = await asyncio.to_thread(LocalEngine)
            except Exception:
                logger.exception("Speech models unavailable; run explicit speech setup")
        yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(BodyLimit)

    def require_engine():
        if state["engine"] is None:
            raise HTTPException(503, "Speech models unavailable; run speech setup")
        return state["engine"]

    async def infer(method, *args):
        model = require_engine()
        if not lock.acquire(blocking=False):
            raise HTTPException(429, "Speech service busy; retry shortly")

        def work():
            try:
                return getattr(model, method)(*args)
            finally:
                lock.release()

        # Shield retains the CPU lock until inference really ends after a timeout.
        task = asyncio.create_task(asyncio.to_thread(work))
        task.add_done_callback(lambda done: done.exception() if not done.cancelled() else None)
        try:
            return await asyncio.wait_for(asyncio.shield(task), INFERENCE_TIMEOUT)
        except TimeoutError as exc:
            raise HTTPException(504, "Speech processing timed out") from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except Exception as exc:
            logger.exception("Speech inference failed")
            raise HTTPException(503, "Speech processing failed; please retry") from exc

    @app.get("/health")
    def health():
        return {"available": state["engine"] is not None}

    @app.get("/voices")
    def voices():
        model = state["engine"]
        return {"items": model.voices() if model else [], "available": model is not None}

    @app.post("/transcribe")
    async def transcribe(audio: UploadFile):
        try:
            data = await audio.read(MAX_UPLOAD + 1)
        finally:
            await audio.close()
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, "Audio exceeds 2 MiB")
        if not data:
            raise HTTPException(422, "Audio is empty")
        return await infer("transcribe", data)

    @app.post("/synthesize")
    async def synthesize(request: Synthesis):
        if request.voice_id not in {v["id"] for v in require_engine().voices()}:
            raise HTTPException(422, "Unknown preset voice")
        data = await infer("synthesize", request.text, request.voice_id)
        return Response(data, media_type="audio/wav", headers={"Cache-Control": "no-store"})

    return app


app = create_app()
