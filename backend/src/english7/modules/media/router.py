import os
from io import BytesIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from minio import Minio
from sqlalchemy import select

from english7.core.settings import get_settings
from english7.db.models import AudioTrack, MediaAsset
from english7.db.session import get_session_factory

router = APIRouter(prefix="/media", tags=["media"])


def _get_minio_client() -> Minio | None:
    settings = get_settings()
    if not settings.minio_endpoint or not settings.minio_access_key or not settings.minio_secret_key:
        return None
    endpoint = settings.minio_endpoint
    secure = endpoint.startswith("https://")
    endpoint = endpoint.removeprefix("https://").removeprefix("http://")
    return Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key.get_secret_value(),
        secure=secure,
    )


@router.get("/audio/{track_number}")
def get_audio_by_track(track_number: int) -> Response:
    asset = None
    if get_settings().database_url:
        try:
            with get_session_factory()() as session:
                track = session.scalar(
                    select(AudioTrack).where(AudioTrack.track_number == track_number)
                )
                if track:
                    asset = session.scalar(
                        select(MediaAsset).where(MediaAsset.id == track.media_asset_id)
                    )
        except Exception:
            asset = None

    data: bytes | None = None
    minio_client = _get_minio_client()
    if asset and minio_client:
        try:
            response = minio_client.get_object(asset.bucket, asset.object_key)
            data = response.read()
            response.close()
            response.release_conn()
        except Exception:
            data = None

    if data is None and minio_client:
        # Fallback to direct object key conventions
        candidate_keys = [
            f"audio/track-{track_number:02d}.mp3",
            f"audio/{track_number:03d}.mp3",
        ] + [f"audio/review-{r}-track-{track_number:02d}.mp3" for r in range(1, 5)] + [f"audio/unit-{u}-track-{track_number:02d}.mp3" for u in range(1, 13)]
        for unit_key in candidate_keys:
            try:
                response = minio_client.get_object("english7-media", unit_key)
                data = response.read()
                response.close()
                response.release_conn()
                if data:
                    break
            except Exception:
                pass

    if data is None:
        # Fallback to local files if available
        local_candidates = [
            f"/tmp/audio/{track_number:03d}.mp3",
            f"/home/nguyenphuong/Music/MP3_Tieng anh 7_Global Success/{track_number:03d}.mp3",
        ]
        for candidate in local_candidates:
            if os.path.exists(candidate):
                with open(candidate, "rb") as f:
                    data = f.read()
                break

    if data is None:
        raise HTTPException(status_code=404, detail="Audio track not found")

    return Response(
        content=data,
        media_type="audio/mpeg",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(data)),
            "Content-Disposition": f'inline; filename="track-{track_number:02d}.mp3"',
            "Cache-Control": "public, max-age=86400",
        },
    )


@router.get("/image/{filename}")
@router.get("/images/{filename}")
def get_image_by_filename(filename: str) -> Response:
    clean_filename = os.path.basename(filename)
    if not clean_filename or clean_filename != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    ext = os.path.splitext(clean_filename)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    data: bytes | None = None
    minio_client = _get_minio_client()
    if minio_client:
        for key in [f"images/{clean_filename}", clean_filename]:
            try:
                response = minio_client.get_object("english7-media", key)
                data = response.read()
                response.close()
                response.release_conn()
                if data:
                    break
            except Exception:
                pass

    if data is None:
        local_dirs = [
            os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images"),
            "/app/assets/images",
            "/tmp/images",
        ]
        for d in local_dirs:
            p = os.path.join(d, clean_filename)
            if os.path.exists(p) and os.path.isfile(p):
                with open(p, "rb") as f:
                    data = f.read()
                break

    if data is None:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(
        content=data,
        media_type=media_type,
        headers={
            "Content-Length": str(len(data)),
            "Content-Disposition": f'inline; filename="{clean_filename}"',
            "Cache-Control": "public, max-age=86400",
        },
    )

