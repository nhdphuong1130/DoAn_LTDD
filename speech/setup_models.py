"""Explicit model download/warmup; never invoked by the core API."""
import json
import os
import shutil
import tempfile

from speech.engine import ASR_REPO, CACHE, CODEC_REPO, TTS_REPO, LocalEngine, configure_cache


def materialize_snapshots():
    """Migrate previous HF symlinks without disabling ONNX path validation."""
    hub = CACHE / "huggingface" / "hub"
    for snapshot in hub.glob("models--*/snapshots/*"):
        for path in snapshot.rglob("*"):
            if path.is_symlink() and path.is_file():
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
                    temporary = output.name
                    with path.open("rb") as source:
                        shutil.copyfileobj(source, output)
                os.replace(temporary, path)


def main():
    configure_cache(offline=False)
    CACHE.mkdir(parents=True, exist_ok=True)
    materialize_snapshots()
    if (CACHE / "ready.json").is_file():
        engine = LocalEngine()
        print("Reusing existing offline model cache:", CACHE)
    else:
        engine = LocalEngine(setup=True)
        # Warmup covers phonemizer assets that may be loaded lazily by upstream.
        engine.synthesize("Xin chào. Em hãy đọc lại từ này nhé.", engine.voices()[0]["id"])
        models = {}
        for repo in (ASR_REPO, TTS_REPO, CODEC_REPO):
            ref = CACHE / "huggingface" / "hub" / ("models--" + repo.replace("/", "--")) / "refs" / "main"
            models[repo] = ref.read_text().strip()
        (CACHE / "ready.json").write_text(json.dumps({"models": models}, indent=2) + "\n")
    print(json.dumps({"voices": engine.voices(), "cache": str(CACHE)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
