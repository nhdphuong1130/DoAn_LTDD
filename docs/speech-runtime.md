# Local speech runtime

The optional CPU service transcribes short English recordings with faster-whisper
and reads Vietnamese feedback with VieNeu-TTS v3 Turbo. There is no paid API,
GPU dependency, voice cloning endpoint, or invented pronunciation score. Models
download during explicit setup; application inference uses the existing cache
with `HF_HUB_OFFLINE=1`. Flashcards remain usable when speech is unavailable.

## Setup and start

Run from the repository root with Python 3.12, `uv`, and Docker Compose installed:

```bash
make speech-setup
make test-speech
make speech-up
curl --fail http://127.0.0.1:8010/health
make speech-down
```

`speech-setup` creates `speech/.venv`, installs `speech/requirements.txt`, downloads
the public model files, warms Vietnamese synthesis, and records model revisions in
`speech/.cache/ready.json`. Setup requires internet but no token. An interrupted
download can be resumed by running it again. A ready cache is reused offline.
For dependency-only installation, without downloading models, run
`bash scripts/setup_speech.sh --deps-only`.

`speech-up` starts the core stack and the optional `compose.speech.yml` service.
The first Docker build downloads Python packages separately from the host venv.
The existing model cache is mounted into the container and excluded from the image.
The backend connects to `http://speech-runtime:8010` on the Compose network;
the diagnostic host port is published only on `127.0.0.1:8010`. Do not expose this
unauthenticated internal service to other machines. The student-facing backend
enforces authentication and ownership.

Core-only `make up`/`make run` may label the optional speech container an
"orphan" because it is defined in the overlay; this warning is expected. Do not
add `--remove-orphans` to startup commands. `make down` intentionally removes all
project containers, including speech, while retaining database volumes/model cache.

For backend development outside Docker, run `speech/.venv/bin/python -m speech`
and set `ENGLISH7_SPEECH_RUNTIME_URL=http://127.0.0.1:8010` in that backend's shell.
Run only one speech process at a time. The container has a four-CPU, 4 GiB memory
limit; both model engines use four CPU threads and requests are serialized.
The overlay sets `OPENBLAS_NUM_THREADS=1` for the small NumPy projections;
otherwise BLAS starts twelve threads on this laptop and exhausts the four-CPU
quota alongside ONNX.

## Models, voices, and licenses

| Component | Selected version/configuration | License/source |
| --- | --- | --- |
| ASR library | faster-whisper 1.2.1, CTranslate2 4.8.2, CPU INT8 | [MIT](https://github.com/SYSTRAN/faster-whisper) |
| English ASR model | Systran/faster-whisper-base.en | [MIT model card](https://huggingface.co/Systran/faster-whisper-base.en) |
| TTS library | vieneu 3.8.3, ONNX Runtime 1.30.0, CPU FP32 | [Apache-2.0 SDK](https://github.com/pnnbao97/VieNeu-TTS), [MIT ONNX Runtime](https://github.com/microsoft/onnxruntime) |
| Vietnamese TTS model | pnnbao-ump/VieNeu-TTS-v3-Turbo | [Apache-2.0 model and preset assets](https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo#-usage-rights--licensing-faq) |
| Audio codec | OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX | [Apache-2.0](https://huggingface.co/OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX) |
| Phonemizer | sea-g2p 0.10.0 | [Apache-2.0](https://github.com/pnnbao97/sea-g2p) |

VieNeu's current repository also describes a proprietary v4 service. This
integration selects the open-source v3 Turbo. Its model card explicitly includes
the bundled preset embeddings/reference codes under Apache-2.0 and permits use of
generated preset audio. Retain upstream notices when redistributing model assets.
The core dependency inventory is in [dependencies.md](dependencies.md).

The configured presets are **Mai Anh**, **Hải Đăng**, **Thùy Dung**, and
**Thiện Minh**, from the installed SDK's featured voices. The runtime checks that
all four names exist before becoming available. Student accounts select and save
one voice through the backend. These voices read Vietnamese feedback; they are
not a verified English pronunciation reference. Technical waveform checks have
passed; a teacher still needs to listen to the four samples for classroom quality.

Model revisions recorded during verification on 2026-09-26:

```text
Systran/faster-whisper-base.en                3d3d5dee26484f91867d81cb899cfcf72b96be6c
pnnbao-ump/VieNeu-TTS-v3-Turbo                 61b85e3d937fbbacb387714180e8182823512523
OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX   ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae
```

A fresh online setup resolves the upstream model revision available at that time;
retain the ready cache for the exact tested models. Core engine package versions
are pinned. Hugging Face Hub 1.33 uses shared blob symlinks that can conflict with
ONNX Runtime's external-data path checks. Setup materializes existing snapshot
symlinks and disables new cache symlinks, preserving ONNX validation. This may
temporarily retain both the original blobs and the materialized snapshots.

## Private HTTP contract and failure handling

| Route | Request | Response |
| --- | --- | --- |
| `GET /health` | — | `{available: boolean}` |
| `GET /voices` | — | `{items: [{id, name}], available: boolean}` |
| `POST /transcribe` | multipart `audio` | `{transcript, model}` |
| `POST /synthesize` | JSON `{text, voice_id}` | PCM16 WAV at 48 kHz, `Cache-Control: no-store` |

Uploads are limited to 2 MiB and decoded duration to 16 seconds (15-second UI
limit plus one second encoder tolerance). Empty, silent, invalid and too-long
audio is rejected. TTS accepts at most 400 characters and the four named presets.
Concurrent inference returns 429; unavailable models return 503; inference taking
more than 120 seconds returns 504. A timed-out worker keeps the inference lock
until it actually finishes, preventing overlapping CPU jobs. Runtime error
details are logged locally and sanitized in HTTP responses. Multipart upload
buffers (including temporary spooled files) are closed immediately after reading;
inference uses the decoded in-memory recording. The service does not retain it.

## Repeatable offline smoke test

Use a real English clip no longer than 15 seconds and its known phrase:

```bash
speech/.venv/bin/python -m speech.smoke /path/to/english.wav --expected 'known phrase'
```

This diagnostic blocks Python socket connections before loading the models,
asserts that the phrase occurs in the real ASR result, and produces all four
Vietnamese voice samples under the ignored `speech/.cache/smoke-voice-*.wav`.
It checks finite non-silent 48 kHz samples, reports timings and peak Linux RSS,
and never substitutes fake inference. Samples are for listening review, not a
measure of phoneme-level accuracy.

The measured English fixture was the 11-second
[JFK test recording in OpenAI Whisper](https://github.com/openai/whisper/blob/main/tests/jfk.flac)
(SHA-256 `63a4b1e4c1dc655ac70961ffbf518acd249df237e5a0152faae9a4a836949715`).
ASR returned the complete expected sentence, including
`ask not what your country can do for you`.

On an Intel Core i5-13420H Linux laptop, with four inference threads and a warm
filesystem cache: loading both models took 2.10 s, English ASR 0.67 s, and the
Vietnamese phrase `Xin chào. Em hãy đọc lại từ này nhé.` took 1.43–3.40 s across
the four presets. Generated clips were 2.00–2.40 s long. Peak process RSS was
1,464.5 MiB. Resumed online setup plus first warmup took 73.23 s and peaked at
1,443.7 MiB; that is not a full cold-download measurement. The materialized model
cache occupied about 1.4 GiB and the host Python environment about 992 MiB.
These are single-run observations, not concurrency or latency guarantees.

The Docker image was built and the container reached healthy status on this
machine. The image reports 424 MB of content (about 1.75 GB local Docker storage).
A subsequent source-only build reused every dependency layer and took about
three seconds; the initial package download was slow and took over 30 minutes
on the observed connection. Preserve Docker's build cache between source edits.
Both the host and container unit suites passed all 11 tests; the backend container
also reached the runtime by its Compose service name.

With the four-CPU container limit and BLAS restricted to one thread, the actual
151-character Vietnamese mismatch feedback returned HTTP 200 `audio/wav` in
4.82 s and produced 9.20 s of finite, non-silent 48 kHz PCM16 audio. The same
request with the previous twelve-thread BLAS default took 43.29 s and showed
heavy CPU throttling. Container memory after synthesis was about 1.92 GiB of its
4 GiB limit. These two samples had stochastic TTS output and normal concurrent
laptop workloads; they show the observed improvement, not a benchmark guarantee.
