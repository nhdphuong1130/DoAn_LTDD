from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImageFormat:
    media_type: str
    extension: str


def detect_image_format(content: bytes) -> ImageFormat | None:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ImageFormat("image/png", "png")
    if content.startswith(b"\xff\xd8\xff"):
        return ImageFormat("image/jpeg", "jpg")
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ImageFormat("image/webp", "webp")
    return None
