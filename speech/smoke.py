"""Offline inference check using a caller-supplied English recording."""
import argparse
import io
import json
from pathlib import Path
import resource
import socket
import time

from speech.engine import CACHE, LocalEngine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--expected", required=True, help="Phrase the real recording contains")
    args = parser.parse_args()

    def deny_network(*_args, **_kwargs):
        raise RuntimeError("Offline smoke test attempted a network connection")

    socket.socket.connect = deny_network
    started = time.perf_counter()
    engine = LocalEngine()
    result = {"load_seconds": round(time.perf_counter() - started, 3)}
    started = time.perf_counter()
    transcript = engine.transcribe(args.audio.read_bytes())
    result["asr_seconds"] = round(time.perf_counter() - started, 3)
    result.update(transcript)
    if args.expected.casefold() not in transcript["transcript"].casefold():
        raise RuntimeError(f"Expected phrase missing from actual transcript: {transcript}")

    import numpy as np
    import soundfile as sf

    result["voices"] = []
    for index, voice in enumerate(engine.voices()):
        started = time.perf_counter()
        wav = engine.synthesize("Xin chào. Em hãy đọc lại từ này nhé.", voice["id"])
        elapsed = time.perf_counter() - started
        audio, rate = sf.read(io.BytesIO(wav))
        if rate != 48000 or not np.isfinite(audio).all() or np.max(np.abs(audio)) < 0.001:
            raise RuntimeError("TTS did not produce finite, audible 48 kHz samples")
        output = CACHE / f"smoke-voice-{index + 1}.wav"
        output.write_bytes(wav)
        result["voices"].append({"id": voice["id"], "seconds": round(elapsed, 3),
                                 "duration": round(len(audio) / rate, 3), "file": str(output)})
    result["peak_rss_mib"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
