from pathlib import Path
from uuid import uuid4
import pytest

from english7.api.errors import ApplicationError
from english7.modules.flashcards.audio_cache import VocabAudioCache


class FakeSpeechRuntime:
    def __init__(self):
        self.calls = []

    def synthesize(self, text: str, voice_id: str) -> bytes:
        self.calls.append((text, voice_id))
        return b"RIFFfakeaudioWAVEfmt "


def test_cache_miss_synthesizes_and_caches(tmp_path: Path):
    runtime = FakeSpeechRuntime()
    cache = VocabAudioCache(cache_dir=tmp_path, runtime=runtime)
    audio = cache.get_or_synthesize("community", "Mai Anh")
    assert audio == b"RIFFfakeaudioWAVEfmt "
    assert len(runtime.calls) == 1
    assert runtime.calls[0] == ("community", "Mai Anh")

    # Second call should hit disk cache without re-synthesizing
    cached_audio = cache.get_or_synthesize("community", "Mai Anh")
    assert cached_audio == b"RIFFfakeaudioWAVEfmt "
    assert len(runtime.calls) == 1


def test_cache_normalizes_word_and_strips_whitespace(tmp_path: Path):
    runtime = FakeSpeechRuntime()
    cache = VocabAudioCache(cache_dir=tmp_path, runtime=runtime)
    audio1 = cache.get_or_synthesize("  Community  ", "Mai Anh")
    audio2 = cache.get_or_synthesize("community", "Mai Anh")
    assert audio1 == audio2
    assert len(runtime.calls) == 1


def test_cache_raises_when_runtime_fails(tmp_path: Path):
    class BrokenRuntime:
        def synthesize(self, text: str, voice_id: str) -> bytes:
            raise ApplicationError("speech_failed", "Speech service unavailable", 503)

    cache = VocabAudioCache(cache_dir=tmp_path, runtime=BrokenRuntime())
    with pytest.raises(ApplicationError) as exc_info:
        cache.get_or_synthesize("hello", "Mai Anh")
    assert exc_info.value.status_code == 503
