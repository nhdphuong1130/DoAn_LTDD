"""Model boundary. Imports heavy dependencies only inside the optional runtime."""
import io
import json
import os
from pathlib import Path

CACHE = Path(os.environ.get("SPEECH_CACHE_DIR", Path(__file__).parent / ".cache")).resolve()
ASR_REPO = "Systran/faster-whisper-base.en"
TTS_REPO = "pnnbao-ump/VieNeu-TTS-v3-Turbo"
CODEC_REPO = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"
VOICE_IDS = ("Mai Anh", "Hải Đăng", "Thùy Dung", "Thiện Minh")
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
        from vieneu import Vieneu

        if not setup and not (CACHE / "ready.json").is_file():
            raise RuntimeError("Run scripts/setup_speech.sh before starting speech")
        self.asr = WhisperModel(ASR_REPO, device="cpu", compute_type="int8", cpu_threads=4,
                                local_files_only=not setup)
        self.tts = Vieneu(mode="v3turbo", backend="onnx", device="cpu", precision="fp32", threads=4)
        presets = {voice_id: label for label, voice_id in self.tts.list_preset_voices()}
        self._voices = [{"id": v, "name": v} for v in VOICE_IDS if v in presets]
        if len(self._voices) != len(VOICE_IDS):
            raise RuntimeError("Installed VieNeu presets do not match the configured voice list")
        self.model = "faster-whisper-1.2.1/base.en"
        if (CACHE / "ready.json").is_file():
            revision = json.loads((CACHE / "ready.json").read_text())["models"][ASR_REPO]
            self.model += "@" + revision

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
        import soundfile as sf
        audio = self.tts.infer(text, voice=voice_id, max_new_frames=300, max_chars=200,
                               apply_watermark=False)
        if not len(audio):
            raise RuntimeError("Speech synthesis returned empty audio")
        output = io.BytesIO()
        sf.write(output, audio, self.tts.sample_rate, format="WAV", subtype="PCM_16")
        return output.getvalue()
