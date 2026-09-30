# Flashcards and Speaking Implementation Plan

**Goal:** Implement private/published flashcards, review scheduling and free local speech practice with transcript, selectable VieNeu feedback voices and persistent learning progress.

**Architecture:** Authenticated FastAPI routes call services with SQL repositories. Voice inference is an optional private HTTP service, isolated from core API and OCR. Flutter uses a dedicated LearningApi contract supplied by StudentApi; existing quiz progress remains intact.

**Tech Stack:** SQLAlchemy/SQL Server, FastAPI, Flutter, Android native audio capture, faster-whisper, VieNeu-TTS CPU.

## Shared API contract (all routes under /api/v1)

All routes require student role; no caller-supplied user IDs. JSON dates ISO UTC.

- GET /flashcards/decks → {items:[{id,name,kind:"textbook"|"personal",unit_number:null|int,card_count:int}]}
- POST /flashcards/decks {name} → deck; PATCH /flashcards/decks/{id} {name}; DELETE → 204 (personal only).
- GET /flashcards/decks/{id}/cards → {items:[card]}
- POST /flashcards/decks/{id}/cards {word,meaning,example,notes,image_url?,source_card_id?} → card.
- PATCH /flashcards/cards/{id} {word?,meaning?,example?,notes?,image_url?,deck_id?} → card; DELETE → 204.
- card: {id,deck_id,word,meaning,example,notes,image_url,ipa,pos,source_label,source_fragment_id,unit_number,page,audio_url,difficult,due_at,review_count}.
- GET /flashcards/review?deck_id=... → {items:[card]} (new/due, limit 20).
- POST /flashcards/cards/{id}/review {request_id:UUID,answer:string,rating:"again"|"hard"|"good"} → {correct:bool,meaning:string,due_at:string}; answer is recalled English word, normalized by server; schedule cannot advance on wrong recall. Idempotent per user/request ID with payload conflict rejection.
- PATCH /flashcards/cards/{id}/flag {difficult:bool} → card.
- GET /learning/progress → {reviewed_cards:int,due_cards:int,difficult_cards:int,speaking_count:int,recent_speaking:[speaking_result]}.
- GET /speaking/voices → {items:[{id,name}],selected_voice:string|null,available:bool}.
- PUT /speaking/voice {voice_id} → {voice_id}.
- POST /speaking/preview {voice_id} → audio/wav.
- POST /speaking/attempts/{request_id}?card_id=UUID&voice_id=... multipart field audio → speaking_result.
- speaking_result: {id,card_id,prompt,transcript,match_percent,feedback,source_label,created_at,missing_words:[string],extra_words:[string]}.
- POST /speaking/attempts/{id}/audio → audio/wav (owns attempt; text comes from saved feedback).
- GET /speaking/history → {items:[speaking_result]}.

Speech prompts are card.word for first release, not unverified example sentences. No phoneme scoring claims. English sample audio is supplied only if verified; show unavailable otherwise. Personal cards may still be read and compared with their text.

## Task 1 — Flashcard backend

Files: backend/src/english7/modules/flashcards/{models,domain,repository,service,router}.py;
backend/tests/modules/flashcards/test_flashcards.py.
Write failing service/repository/API tests for owner isolation, published read-only cards, copy provenance, duplicate detection, CRUD/move, due scheduling and retry idempotency. Implement SQL-backed services and routes matching contract. Ground textbook seed cards by joining existing ontology vocabulary to verified source fragments with real printed pages; do not invent citations. Repository is infrastructure; policy in service. Deterministic clock in scheduling. Root integrates models/router/migration.

## Task 2 — Mobile learning features

Files: mobile/lib/app/learning_api.dart; mobile/lib/features/flashcards/; mobile/lib/features/speaking/;
mobile/lib/services/speech_recorder.dart; Android capture class and manifest;
mobile/test/features/learning_flow_test.dart.
Define typed API models matching contract, screens for decks/cards/review and speech recording/result/voice selector. Test with fakes before implementation. Existing navigation gains one Learning destination; retain all existing destinations. Inject APIs and recorder for tests. Handle permission denial, loading, retries, empty, submit idempotency, disposal; 15-second bounded audio, never auto-upload. Root wires API transport and navigation/progress.

## Task 3 — Optional local speech runtime

Files: speech/; scripts/setup_speech.sh; compose.speech.yml; docs/speech-runtime.md.
Independent CPU service exposes GET /health, GET /voices, POST /transcribe (audio multipart), POST /synthesize {text,voice_id}. Use pinned compatible dependencies verified from upstream; faster-whisper and VieNeu-TTS run locally with model caching. Download/install is explicit setup, inference does not depend on paid API. Bound audio and request duration, reject silence, serialize CPU model access. Unit tests stub model boundaries; run an actual inference smoke test if model downloads succeed. Report exact versions, resources and blockers. No clone of user voices.

## Task 4 — Integration, speaking API, persistence

Files: backend/src/english7/modules/speaking/; backend/alembic/versions/0007_learning.py;
backend/src/english7/api/router.py; backend/src/english7/db/models.py; mobile/lib/app/{student_api,api_student_api,english7_app}.dart; mobile/lib/features/progress/progress_screen.dart.
Write backend tests for transcript comparison, silence, permissions, idempotency and voice settings. Persist attempt snapshot and model identity; raw student audio temporary only. Proxy internal runtime with bounded input and timeouts. Do not expose runtime publicly. Add authenticated binary transport to Flutter; speech fails gracefully while flashcards remain usable. Migration adds only new tables. Seed verified textbook vocabulary via Makefile command.

## Task 5 — Verification and rollout

Run focused suites, make test, make analyze, git diff --check; inspect SQL Server migration and live endpoints. Preserve earlier uncommitted work. Add source/SPDX headers, dependencies inventory, changelog and startup documentation. Launch updated Android app, check new screen. Distinguish tested application flow from any unavailable external model download. No silent fake transcription or TTS fallback.

## Verification record — 2026-09-26

- `make test`: 6 launcher, 200 backend, 63 Flutter tests passed; `make analyze`: no issues.
- `make test-speech`: 11 passed (upstream TestClient/httpx deprecation warning only).
- SQL Server migrated to `0007_learning`; 15 verified textbook cards seeded across 10 Units; repeat seed added 0.
- Live SQL CRUD/reviews/speaking retry/history smoke passed with all test records rolled back.
- Real 11-second English clip passed through backend → Docker ASR → SQL history → Vietnamese feedback WAV; expected text matched, retry did not create another result.
- Installed current debug APK on Pixel_10_Pro emulator; saved session restored and learning/deck screens loaded from live API.
- Docker speech healthy with four voices; local models cached for subsequent starts. See `docs/speech-runtime.md` for versions, licenses and actual timing/RAM measurements.
- Review fixes verified: pre-multipart upload cap, blank recall, recording-error guidance, frozen migration schema and versioned review snapshots.
- Remaining human acceptance: microphone recording on a physical student device and teacher listening review of voice quality. Transcript matching is not phoneme-level pronunciation grading.
