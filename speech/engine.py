"""Model boundary. Imports heavy dependencies only inside the optional runtime."""
import io
import json
import os
from pathlib import Path

CACHE = Path(os.environ.get("SPEECH_CACHE_DIR", Path(__file__).parent / ".cache")).resolve()
ASR_REPO = "Systran/faster-whisper-base.en"
VOICE_IDS = ("en-GB-SoniaNeural", "en-GB-RyanNeural", "en-US-JennyNeural", "en-US-GuyNeural")
VOICE_LABELS = {
    "en-GB-SoniaNeural": "Sonia (Anh - Anh, Nữ)",
    "en-GB-RyanNeural": "Ryan (Anh - Anh, Nam)",
    "en-US-JennyNeural": "Jenny (Anh - Mỹ, Nữ)",
    "en-US-GuyNeural": "Guy (Anh - Mỹ, Nam)",
}
SAMPLE_RATE = 16000
MAX_SAMPLES = 16 * SAMPLE_RATE  # 15-second UI limit + encoder/stop tolerance.


def configure_cache(*, offline=True):
    os.environ["HF_HOME"] = str(CACHE / "huggingface")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1" if offline else "0"
    # ONNX external tensor files must resolve inside the graph directory.
    os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"


def decode_audio(data):
    """Bound decoded samples too: a small compressed file can contain hours."""
    import av
    import numpy as np

    samples = []
    count = 0
    try:
        with av.open(io.BytesIO(data)) as container:
            if not container.streams.audio:
                raise ValueError("Invalid audio recording")
            resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
            for frame in container.decode(audio=0):
                for converted in resampler.resample(frame):
                    array = converted.to_ndarray().flatten()
                    count += array.size
                    if count > MAX_SAMPLES:
                        raise ValueError("Recording exceeds 15 seconds plus 1 second tolerance")
                    samples.append(array)
            for converted in resampler.resample(None):
                array = converted.to_ndarray().flatten()
                count += array.size
                if count > MAX_SAMPLES:
                    raise ValueError("Recording exceeds 15 seconds plus 1 second tolerance")
                samples.append(array)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Invalid audio recording") from exc
    audio = np.concatenate(samples) if samples else np.array([], dtype=np.float32)
    if len(audio) < SAMPLE_RATE * 0.15 or not np.isfinite(audio).all():
        raise ValueError("Recording is empty or too short")
    if float(np.sqrt(np.mean(audio * audio))) < 0.001:
        raise ValueError("No speech detected; please record again")
    return audio


class LocalEngine:
    def __init__(self, *, setup=False):
        configure_cache(offline=not setup)
        from faster_whisper import WhisperModel

        if not setup and not (CACHE / "ready.json").is_file():
            raise RuntimeError("Run scripts/setup_speech.sh before starting speech")
        self.asr = WhisperModel(ASR_REPO, device="cpu", compute_type="int8", cpu_threads=4,
                                local_files_only=not setup)
        self._voices = [{"id": v, "name": VOICE_LABELS.get(v, v)} for v in VOICE_IDS]
        self.model = "faster-whisper-1.2.1/base.en"
        if (CACHE / "ready.json").is_file():
            ready_data = json.loads((CACHE / "ready.json").read_text())
            if "models" in ready_data and ASR_REPO in ready_data["models"]:
                self.model += "@" + ready_data["models"][ASR_REPO]

    def voices(self):
        return self._voices

    def transcribe(self, data):
        audio = decode_audio(data)
        segments, _ = self.asr.transcribe(audio, language="en", beam_size=5,
                                          vad_filter=True, condition_on_previous_text=False,
                                          vad_parameters={"min_silence_duration_ms": 300})
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        if not transcript:
            raise ValueError("No speech detected; please record again")
        return {"transcript": transcript, "model": self.model}

    def synthesize(self, text, voice_id):
        import asyncio
        import av
        import edge_tts

        if voice_id not in VOICE_IDS:
            raise ValueError(f"Unknown preset voice: {voice_id}")

        async def _synthesize():
            communicate = edge_tts.Communicate(text, voice_id)
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b"".join(chunks)

        mp3_bytes = asyncio.run(_synthesize())
        if not mp3_bytes:
            raise RuntimeError("Speech synthesis returned empty audio")

        input_io = io.BytesIO(mp3_bytes)
        output_io = io.BytesIO()
        with av.open(input_io) as in_container:
            with av.open(output_io, mode="w", format="wav") as out_container:
                out_stream = out_container.add_stream("pcm_s16le", rate=SAMPLE_RATE)
                for frame in in_container.decode(audio=0):
                    for packet in out_stream.encode(frame):
                        out_container.mux(packet)
                for packet in out_stream.encode(None):
                    out_container.mux(packet)
        return output_io.getvalue()

