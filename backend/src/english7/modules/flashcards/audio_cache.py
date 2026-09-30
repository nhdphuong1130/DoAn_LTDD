import hashlib
import os
from pathlib import Path
import tempfile
from typing import Protocol


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str, voice_id: str) -> bytes: ...


class VocabAudioCache:
    def __init__(self, cache_dir: Path, runtime: SpeechSynthesizer, default_voice: str = "en-GB-SoniaNeural"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.runtime = runtime
        self.default_voice = default_voice

    def _file_path(self, word: str, voice_id: str) -> Path:
        normalized = word.strip().casefold()
        key = hashlib.sha256(f"{normalized}:{voice_id}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.wav"

    def get_or_synthesize(self, word: str, voice_id: str | None = None) -> bytes:
        voice = voice_id or self.default_voice
        target = self._file_path(word, voice)
        if target.is_file() and target.stat().st_size > 0:
            return target.read_bytes()
        clean_word = word.strip()
        audio = self.runtime.synthesize(clean_word, voice)
        if audio:
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, delete=False) as tmp:
                tmp.write(audio)
                tmp_path = Path(tmp.name)
            os.replace(tmp_path, target)
        return audio
