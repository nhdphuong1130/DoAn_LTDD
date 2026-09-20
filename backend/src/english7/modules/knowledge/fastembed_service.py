from collections.abc import Sequence
import threading
from fastembed import TextEmbedding


class FastEmbedService:
    _instance = None
    _lock = threading.Lock()

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_dir: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    def embed(self, text: str) -> list[float]:
        cleaned = text.strip() if text else "empty"
        embeddings = list(self._model.embed([cleaned]))
        return [float(x) for x in embeddings[0]]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        cleaned = [t.strip() if t and t.strip() else "empty" for t in texts]
        embeddings = list(self._model.embed(cleaned))
        return [[float(x) for x in emb] for emb in embeddings]
