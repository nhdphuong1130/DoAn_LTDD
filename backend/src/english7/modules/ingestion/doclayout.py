from collections.abc import Callable

from english7.modules.ingestion.contracts import DetectedRegion, RenderedPage


class DocLayoutDetector:
    """Thin adapter around an optionally installed DocLayout-YOLO predictor."""

    def __init__(
        self,
        *,
        model_id: str,
        confidence_threshold: float,
        predictor: Callable[[bytes, str], list[DetectedRegion]],
    ) -> None:
        if not model_id.strip():
            raise ValueError("A layout model identifier is required")
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("Layout confidence threshold must be between 0 and 1")
        self.version = model_id
        self._threshold = confidence_threshold
        self._predictor = predictor

    def detect(self, page: RenderedPage) -> list[DetectedRegion]:
        return [
            region
            for region in self._predictor(page.image, self.version)
            if region.confidence >= self._threshold
        ]
