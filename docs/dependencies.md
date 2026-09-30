<!--
-->

# Dependencies Inventory

This document inventories all external upstream open-source dependencies across the backend, mobile, and infrastructure layers.

## Backend (Python 3.12)

Managed via `uv` in `backend/pyproject.toml` and locked in `backend/uv.lock`.

| Dependency | Version Floor | License | Rationale / Purpose |
|---|---|---|---|
| `fastapi` | `>=0.116,<1` | MIT | Asynchronous REST API framework |
| `uvicorn[standard]` | `>=0.35,<1` | BSD-3-Clause | ASGI web server runtime |
| `sqlalchemy` | `>=2.0.41,<3` | MIT | ORM and SQL abstraction |
| `pyodbc` | `>=5.2,<6` | MIT | High-performance ODBC driver for Microsoft SQL Server |
| `alembic` | `>=1.16,<2` | MIT | Database schema migration manager |
| `neo4j` | `>=5.28,<6` | Apache-2.0 | Official Bolt driver for Neo4j Knowledge Graph |
| `fastembed` | `>=0.8,<0.9` | Apache-2.0 | Fast, local CPU embedding inference (`BAAI/bge-small-en-v1.5`, 384d) |
| `minio` | `>=7.2,<8` | Apache-2.0 | S3-compatible client for lesson audio and image assets |
| `argon2-cffi` | `>=25.1,<26` | MIT | Secure password hashing using Argon2id |
| `PyJWT` | `>=2.10,<3` | MIT | JSON Web Token encoding and decoding |
| `pydantic-settings` | `>=2.10,<3` | MIT | Type-safe environment configuration management |
| `email-validator` | `>=2.2,<3` | CC0-1.0 | Email validation for student account registration |
| `pytest` | `>=8.4,<9` | MIT | Test framework (dev/test extra) |
| `pytest-cov` | `>=6.2,<7` | MIT | Code coverage reporting (dev/test extra) |
| `httpx2` | `>=2.13,<3` | BSD-3-Clause | TestClient HTTP transport (dev/test extra) |

## Mobile (Flutter / Dart)

Managed via `pubspec.yaml` in `mobile/`.

| Dependency | Version Floor | License | Rationale / Purpose |
|---|---|---|---|
| `flutter` | `>=3.27.0` | BSD-3-Clause | Cross-platform mobile UI framework |
| `http` | `^1.2.2` | BSD-3-Clause | Composable HTTP client for student API communication |
| `flutter_secure_storage` | `^9.2.2` | BSD-3-Clause | Encrypted local storage for student JWT access tokens |
| `audioplayers` | `^6.1.0` | MIT | Low-latency audio playback for listening tracks |
| `flutter_test` | SDK | BSD-3-Clause | Unit and widget test framework |

## Optional speech runtime (CPU, isolated from backend/OCR)

Direct versions are pinned in `speech/requirements.txt`. Installed by
`make speech-setup`; `bash scripts/setup_speech.sh --deps-only` installs only the
test/runtime libraries. No additional Flutter package: Android `AudioRecord`
captures mono PCM WAV through a platform channel; `MediaPlayer` plays audio.

| Dependency | Version | License | Purpose |
|---|---|---|---|
| `vieneu` | 3.8.3 | Apache-2.0 | Vietnamese preset-voice feedback, ONNX CPU backend |
| `faster-whisper` | 1.2.1 | MIT | Local English speech recognition |
| `fastapi` / `uvicorn` | 0.135.1 / 0.42.0 | MIT / BSD-3-Clause | Private HTTP runtime |
| `python-multipart` | 0.0.22 | Apache-2.0 | Bounded recording uploads |
| `numpy` | 2.3.5 | BSD-3-Clause plus bundled notices | Audio arrays |
| `soundfile` | 0.13.1 | BSD-3-Clause; bundled libsndfile LGPL | WAV encoding |
| `pytest` / `httpx` | 8.4.2 / 0.28.1 | MIT / BSD-3-Clause | Runtime tests |

Key transitives verified in the installed environment: `onnxruntime` 1.30.0
(MIT), `ctranslate2` 4.8.2 (MIT), `sea-g2p` 0.10.0 (Apache-2.0), and
`huggingface-hub` 1.33.0 (Apache-2.0). Preserve upstream bundled dependency notices
when redistributing binaries. Model weights are cached locally, never committed:

- `Systran/faster-whisper-base.en`: MIT.
- `pnnbao-ump/VieNeu-TTS-v3-Turbo`: Apache-2.0, including bundled presets per model card.
- `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX`: Apache-2.0.

Models and first-run phonemizer assets require an Internet download; normal
inference uses local cache. CPU/RAM/electricity costs still apply, despite no
paid API requirement. See [speech runtime](speech-runtime.md) for reproducibility
and model provenance. VieNeu is used for Vietnamese feedback, not an unverified
English pronunciation reference.

## Infrastructure & Services

The local launcher (`make run`) requires Bash, Python 3 (standard-library JSON
parsing and launcher tests), Flutter, and Docker Compose v2 with `up --wait` and
`--wait-timeout` support. It does not install additional Python packages.

Managed via Docker Compose (`infra/docker/compose.yaml`).

| Container Image | Upstream Version | License | Role |
|---|---|---|---|
| `mcr.microsoft.com/mssql/server` | `2022-latest` | Microsoft EULA (Express) | Relational database for accounts, curriculum structure, quizzes |
| `neo4j` | `5.26-community` | GPL-3.0 with Classpath Exception | Knowledge graph and dual vector search |
| `minio/minio` | `RELEASE.2025-02-07` | AGPL-3.0 | S3-compatible asset store for audio and images |
