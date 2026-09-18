from collections.abc import Callable

from english7.modules.ingestion.contracts import DetectedRegion, OCRResult, RenderedPage


class ConfiguredOCREngine:
    """Provider-neutral OCR adapter selected by configuration."""

    def __init__(
        self,
        *,
        engine_name: str,
        version: str,
        recognizer: Callable[[RenderedPage, DetectedRegion], OCRResult],
    ) -> None:
        if not engine_name.strip() or not version.strip():
            raise ValueError("OCR engine name and version are required")
        self.engine_name = engine_name
        self.version = version
        self._recognizer = recognizer

    def recognize(self, page: RenderedPage, region: DetectedRegion) -> OCRResult:
        return self._recognizer(page, region)
