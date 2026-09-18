# English 7 GraphRAG MVP Implementation Plan

**Goal:** Build an API-first Flutter/FastAPI MVP that ingests verified Unit 1–2 textbook content, answers only from grounded SGK sources, generates validated quizzes, enforces listening-test rules, and runs consistently through Docker on Linux and Windows.

**Architecture:** Use a modular FastAPI monolith with a separate worker process. SQL Server is the source of truth, Neo4j stores the knowledge graph and vector index, MinIO stores media, and OpenRouter is accessed behind an injectable provider. Flutter consumes only versioned `/api/v1` endpoints.

**Tech Stack:** Python 3.12, FastAPI, Pydantic Settings, SQLAlchemy/Alembic, pyodbc, Neo4j Python driver, MinIO SDK, httpx, pytest, Flutter/Dart, Docker Compose, SQL Server, Neo4j, MinIO.

---

## Delivery strategy

Implement a working vertical slice before expanding breadth:

1. Infrastructure and health checks.
2. API contracts and textbook/source data.
3. Grounded tutor with deterministic fake provider.
4. Quiz/test policy and audio limits.
5. Hierarchical graph-vector fusion adapters and OpenRouter integration.
6. Ingestion jobs and admin review.
7. Flutter student flow.
8. Full verification and cross-platform documentation.

Every behavior-changing task follows red-green-refactor. External systems are tested through adapters; unit tests do not perform network calls.

### Task 1: Repository and backend scaffold

**Files:**
- Create: `README.md`
- Create: `.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/src/english7/__init__.py`
- Create: `backend/src/english7/main.py`
- Create: `backend/src/english7/core/settings.py`
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_health.py`

**Step 1: Write the failing health test**

```python
from fastapi.testclient import TestClient

from english7.main import app


def test_health_returns_service_status() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "english7-api"}
```

**Step 2: Run it and verify RED**

Run: `docker run --rm -v "$PWD/backend:/app" -w /app python:3.12-slim sh -c "pip install -e '.[test]' && pytest tests/test_health.py -q"`

Expected: FAIL because `english7.main` does not exist.

**Step 3: Add the minimum app and validated settings**

`main.py` creates FastAPI and exposes `/api/v1/health`. `settings.py` uses `BaseSettings`, `env_file=.env`, and typed fields for service name, database URLs, storage, AI provider, model names, timeouts, retrieval limits, and upload limits. No environment-specific value is embedded in route or service code.

**Step 4: Run GREEN**

Run: `docker run --rm -v "$PWD/backend:/app" -w /app python:3.12-slim sh -c "pip install -e '.[test]' && pytest tests/test_health.py -q"`

Expected: `1 passed`.

**Step 5: Commit**

```bash
git add README.md .env.example backend
git commit -m "build: scaffold FastAPI backend"
```

### Task 2: Docker Compose infrastructure

**Files:**
- Create: `compose.yaml`
- Create: `backend/Dockerfile`
- Create: `backend/docker/entrypoint.sh`
- Create: `scripts/check-compose.sh`
- Modify: `.env.example`
- Modify: `README.md`

**Step 1: Add a failing Compose configuration check**

`scripts/check-compose.sh` must run `docker compose config --quiet` and verify the configured services `api`, `worker`, `sqlserver`, `neo4j`, `minio`, and `minio-init` exist.

Run: `bash scripts/check-compose.sh`

Expected: FAIL because `compose.yaml` is absent.

**Step 2: Add infrastructure with health checks**

- SQL Server persists `/var/opt/mssql` and receives credentials from environment variables.
- Neo4j persists data/logs and receives auth from environment variables.
- MinIO persists `/data`; `minio-init` creates configured buckets idempotently.
- API and worker build the same backend image with different commands.
- No host-specific absolute paths.
- Add optional `gpu` profile only to the ingestion worker extension, not the default worker.

**Step 3: Verify GREEN**

Run: `bash scripts/check-compose.sh`

Expected: PASS and list all six services.

Run: `docker compose --env-file .env.example config --quiet`

Expected: exit 0.

**Step 4: Commit**

```bash
git add compose.yaml backend/Dockerfile backend/docker scripts .env.example README.md
git commit -m "build: add cross-platform Docker services"
```

### Task 3: Common API contracts and error handling

**Files:**
- Create: `backend/src/english7/api/router.py`
- Create: `backend/src/english7/api/errors.py`
- Create: `backend/src/english7/api/schemas.py`
- Modify: `backend/src/english7/main.py`
- Test: `backend/tests/api/test_errors.py`

**Step 1: Write failing tests**

```python
def test_unknown_route_uses_standard_error(client):
    response = client.get("/api/v1/unknown")
    body = response.json()
    assert response.status_code == 404
    assert set(body) == {"code", "message", "details", "trace_id"}


def test_trace_id_is_returned_as_header(client):
    response = client.get("/api/v1/unknown")
    assert response.headers["x-trace-id"] == response.json()["trace_id"]
```

**Step 2: Verify RED**

Run: `pytest backend/tests/api/test_errors.py -q`

Expected: FAIL with FastAPI's default `detail` body.

**Step 3: Implement exception handlers and trace middleware**

Define `ErrorResponse(code, message, details, trace_id)`. Add handlers for application errors, validation errors, HTTP errors, and unexpected exceptions. Generate or propagate `X-Trace-ID`.

**Step 4: Verify GREEN**

Run: `pytest backend/tests/api/test_errors.py -q`

Expected: all tests pass.

**Step 5: Commit**

```bash
git add backend/src/english7/api backend/src/english7/main.py backend/tests/api
git commit -m "feat: standardize API errors and trace IDs"
```

### Task 4: SQL Server persistence and migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial_schema.py`
- Create: `backend/src/english7/db/base.py`
- Create: `backend/src/english7/db/session.py`
- Create: `backend/src/english7/db/models.py`
- Test: `backend/tests/db/test_models.py`
- Test: `backend/tests/integration/test_migrations.py`

**Step 1: Write failing domain/model tests**

Test that:

- `SourceFragment` cannot be published unless verified.
- page number and bounding-box coordinates cannot be negative.
- a `QuizQuestion` must reference at least one source fragment.
- an audio play counter never becomes negative.

**Step 2: Verify RED**

Run: `pytest backend/tests/db/test_models.py -q`

Expected: FAIL because models are absent.

**Step 3: Implement SQLAlchemy models**

Create tables for users, roles, textbooks, units, sections, activities, source documents, source fragments, media assets, audio tracks, quiz blueprints, quizzes, questions, question sources, test attempts, student answers, mastery records, jobs, and audit events. Use UUID identifiers, UTC timestamps, explicit constraints, and enums stored as strings.

**Step 4: Add and verify migration**

Run: `docker compose up -d sqlserver`

Run: `docker compose run --rm api alembic upgrade head`

Run: `pytest backend/tests/integration/test_migrations.py -q`

Expected: migration applies from an empty database and all expected tables exist.

**Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic backend/src/english7/db backend/tests/db backend/tests/integration
git commit -m "feat: add SQL Server schema and migrations"
```

### Task 5: Authentication and roles

**Files:**
- Create: `backend/src/english7/modules/auth/domain.py`
- Create: `backend/src/english7/modules/auth/service.py`
- Create: `backend/src/english7/modules/auth/repository.py`
- Create: `backend/src/english7/modules/auth/router.py`
- Create: `backend/src/english7/core/security.py`
- Test: `backend/tests/modules/auth/test_service.py`
- Test: `backend/tests/api/test_auth.py`

**Step 1: Write failing tests**

Cover password hashing, successful login, invalid credentials, expired access token, student forbidden from admin API, and admin access allowed.

**Step 2: Verify RED**

Run: `pytest backend/tests/modules/auth backend/tests/api/test_auth.py -q`

Expected: FAIL because auth service is absent.

**Step 3: Implement minimum auth**

Provide register/login/me endpoints. Read token lifetime and algorithm from validated settings. Store only password hashes. Seed roles `student` and `admin` through a repeatable command.

**Step 4: Verify GREEN**

Run: `pytest backend/tests/modules/auth backend/tests/api/test_auth.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/auth backend/src/english7/core/security.py backend/tests/modules/auth backend/tests/api/test_auth.py
git commit -m "feat: add token authentication and roles"
```

### Task 6: Textbook, source fragments, media, and admin review API

**Files:**
- Create: `backend/src/english7/modules/textbooks/domain.py`
- Create: `backend/src/english7/modules/textbooks/repository.py`
- Create: `backend/src/english7/modules/textbooks/service.py`
- Create: `backend/src/english7/modules/textbooks/router.py`
- Create: `backend/src/english7/modules/media/storage.py`
- Create: `backend/src/english7/modules/admin/router.py`
- Test: `backend/tests/modules/textbooks/test_service.py`
- Test: `backend/tests/api/test_textbooks.py`
- Test: `backend/tests/api/test_admin_review.py`

**Step 1: Write failing tests**

Test list:

- Student lists only published Unit 1–2 content.
- Unverified fragment never appears in student endpoints.
- Admin can correct OCR text and verify a fragment.
- Verification records reviewer and audit event.
- Media URL is generated through storage adapter and never exposes credentials.

**Step 2: Verify RED**

Run: `pytest backend/tests/modules/textbooks backend/tests/api/test_textbooks.py backend/tests/api/test_admin_review.py -q`

**Step 3: Implement services and routes**

Expose `/api/v1/textbooks`, `/api/v1/lessons`, `/api/v1/media`, and `/api/v1/admin/fragments`. Use pagination schemas and repository protocols so unit tests can use in-memory fakes.

**Step 4: Verify GREEN**

Run the same pytest command; expect all tests pass.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/textbooks backend/src/english7/modules/media backend/src/english7/modules/admin backend/tests
git commit -m "feat: expose verified textbook content and review API"
```

### Task 7: Job system and document ingestion interfaces

**Files:**
- Create: `backend/src/english7/modules/jobs/domain.py`
- Create: `backend/src/english7/modules/jobs/service.py`
- Create: `backend/src/english7/modules/jobs/router.py`
- Create: `backend/src/english7/modules/ingestion/contracts.py`
- Create: `backend/src/english7/modules/ingestion/pipeline.py`
- Create: `backend/src/english7/modules/ingestion/doclayout.py`
- Create: `backend/src/english7/modules/ingestion/ocr.py`
- Create: `backend/src/english7/worker.py`
- Test: `backend/tests/modules/ingestion/test_pipeline.py`
- Test: `backend/tests/api/test_jobs.py`

**Step 1: Write failing pipeline tests**

Use fake renderer, layout detector, OCR engine, storage, and repository. Verify the pipeline:

- hashes and registers a source document;
- renders only configured pages;
- stores bounding boxes and confidence scores;
- produces `DRAFT` fragments;
- preserves printed page separately from PDF page;
- marks a failed job with a sanitized error.

**Step 2: Verify RED**

Run: `pytest backend/tests/modules/ingestion backend/tests/api/test_jobs.py -q`

**Step 3: Implement contracts and orchestrator**

The default DocLayout adapter loads model identifiers and thresholds from settings. The OCR adapter is selected through configuration. Heavy dependencies live in an optional `ingestion` dependency group so the API container can stay lightweight.

**Step 4: Verify GREEN**

Run the same tests; expect all pass.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/jobs backend/src/english7/modules/ingestion backend/src/english7/worker.py backend/tests
git commit -m "feat: add asynchronous textbook ingestion pipeline"
```

### Task 8: Neo4j graph builder and hierarchical graph-vector fusion

**Files:**
- Create: `backend/src/english7/modules/knowledge/contracts.py`
- Create: `backend/src/english7/modules/knowledge/neo4j_repository.py`
- Create: `backend/src/english7/modules/knowledge/graph_builder.py`
- Create: `backend/src/english7/modules/retrieval/service.py`
- Create: `backend/src/english7/modules/retrieval/reranker.py`
- Test: `backend/tests/modules/knowledge/test_graph_builder.py`
- Test: `backend/tests/modules/retrieval/test_service.py`
- Test: `backend/tests/integration/test_neo4j.py`

**Step 1: Write failing tests**

Verify:

- only verified fragments are indexed;
- graph nodes keep stable SQL identifiers;
- vector candidates outside configured Units are discarded;
- graph neighbors enrich but cannot replace source evidence;
- candidates follow the `Textbook → Unit → Section → Activity → SourceFragment` hierarchy;
- Reciprocal Rank Fusion combines graph and vector ranks deterministically;
- low-confidence retrieval returns no grounded context;
- citations are deduplicated and consistently ordered.

**Step 2: Verify RED**

Run: `pytest backend/tests/modules/knowledge backend/tests/modules/retrieval -q`

**Step 3: Implement graph builder and retrieval service**

Use parameterized Cypher only. Create indexes/constraints idempotently. Configure embedding dimensions, vector index name, top-k, thresholds, graph depth, and RRF constant externally. Keep the vector index in Neo4j and do not add a separate vector database.

**Step 4: Verify integration**

Run: `docker compose up -d neo4j`

Run: `pytest backend/tests/integration/test_neo4j.py -q`

Expected: nodes, relationships, and vector query operate against the container.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/knowledge backend/src/english7/modules/retrieval backend/tests
git commit -m "feat: add hierarchical graph-vector fusion"
```

### Task 9: OpenRouter provider and grounded AI Tutor

**Files:**
- Create: `backend/src/english7/modules/ai/contracts.py`
- Create: `backend/src/english7/modules/ai/openrouter.py`
- Create: `backend/src/english7/modules/ai/fake.py`
- Create: `backend/src/english7/modules/tutor/service.py`
- Create: `backend/src/english7/modules/tutor/router.py`
- Test: `backend/tests/modules/ai/test_openrouter.py`
- Test: `backend/tests/modules/tutor/test_service.py`
- Test: `backend/tests/api/test_tutor.py`

**Step 1: Write failing tests**

Cover:

- provider sends configured model and timeout;
- API key never appears in logs/errors;
- tutor does not call LLM without grounded context;
- tutor rejects returned citation IDs not present in context;
- Vietnamese and English modes change presentation only, not evidence;
- out-of-scope image/query returns a stable error code.

**Step 2: Verify RED**

Run: `pytest backend/tests/modules/ai backend/tests/modules/tutor backend/tests/api/test_tutor.py -q`

**Step 3: Implement provider and tutor orchestration**

Require structured JSON output containing `answer`, `language`, and `citations`. The service validates citations before returning. Inject fake provider in tests.

**Step 4: Verify GREEN**

Run the same test command; expect all pass.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/ai backend/src/english7/modules/tutor backend/tests
git commit -m "feat: add source-validated bilingual AI tutor"
```

### Task 10: Quiz blueprint, validation, and test attempt policy

**Files:**
- Create: `backend/src/english7/modules/quizzes/domain.py`
- Create: `backend/src/english7/modules/quizzes/blueprint.py`
- Create: `backend/src/english7/modules/quizzes/validator.py`
- Create: `backend/src/english7/modules/quizzes/service.py`
- Create: `backend/src/english7/modules/quizzes/router.py`
- Create: `backend/src/english7/modules/attempts/service.py`
- Test: `backend/tests/modules/quizzes/test_blueprint.py`
- Test: `backend/tests/modules/quizzes/test_validator.py`
- Test: `backend/tests/modules/attempts/test_service.py`
- Test: `backend/tests/api/test_quizzes.py`

**Step 1: Write failing tests**

Test list:

- 15/45/60/custom durations select configured blueprint policies.
- custom duration outside configured bounds is rejected.
- every generated question has a valid answer and source.
- duplicate questions are rejected by configured similarity threshold.
- submitted quiz cannot mutate.
- server clock auto-submits expired attempts.
- audio starts at two remaining plays, decrements atomically, and never resets on resume.
- failed media authorization before playback does not decrement the count.

**Step 2: Verify RED**

Run: `pytest backend/tests/modules/quizzes backend/tests/modules/attempts backend/tests/api/test_quizzes.py -q`

**Step 3: Implement policies through configuration/database**

Do not embed duration-to-question-count rules in route handlers. Load active policy records through a repository. Inject a clock into attempt service for deterministic tests.

**Step 4: Verify GREEN**

Run the same tests; expect all pass.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/quizzes backend/src/english7/modules/attempts backend/tests
git commit -m "feat: add grounded quizzes and listening attempt rules"
```

### Task 11: Seed/import package for Unit 1–2 and audio mapping

**Files:**
- Create: `backend/src/english7/cli.py`
- Create: `backend/src/english7/modules/seeding/manifest.py`
- Create: `backend/src/english7/modules/seeding/importer.py`
- Create: `data/manifests/unit-1-2.example.json`
- Create: `scripts/export-seed.sh`
- Create: `scripts/import-seed.sh`
- Test: `backend/tests/modules/seeding/test_importer.py`

**Step 1: Write failing idempotency tests**

Import the same manifest twice and assert no duplicates. Reject mismatched source hashes, missing audio object keys, invalid page bounds, and unverified fragments marked for publication.

**Step 2: Verify RED**

Run: `pytest backend/tests/modules/seeding/test_importer.py -q`

**Step 3: Implement versioned manifest import/export**

The manifest contains metadata only; copyrighted raw PDF/audio remain ignored. Import command accepts paths as arguments, never absolute paths embedded in code.

**Step 4: Verify GREEN**

Run the same test; expect all pass.

**Step 5: Commit**

```bash
git add backend/src/english7/cli.py backend/src/english7/modules/seeding data/manifests scripts backend/tests/modules/seeding
git commit -m "feat: add reproducible verified content packages"
```

### Task 12: Flutter application scaffold and API client

**Prerequisite:** Install Flutter SDK and Android toolchain, then confirm `flutter doctor` has no blocking Android issue.

**Files:**
- Create: `mobile/pubspec.yaml` and standard Flutter platform files via `flutter create mobile`
- Create: `mobile/lib/config/app_config.dart`
- Create: `mobile/lib/api/api_client.dart`
- Create: `mobile/lib/api/api_error.dart`
- Create: `mobile/lib/features/auth/`
- Create: `mobile/lib/features/lessons/`
- Create: `mobile/lib/features/tutor/`
- Create: `mobile/lib/features/quizzes/`
- Create: `mobile/lib/features/progress/`
- Test: `mobile/test/config/app_config_test.dart`
- Test: `mobile/test/api/api_client_test.dart`

**Step 1: Write failing config/API tests**

Verify the base URL is required through `--dart-define`, normalized without route hardcoding, auth token is attached, trace ID is preserved, and standard backend errors map to typed exceptions.

**Step 2: Verify RED**

Run: `cd mobile && flutter test test/config test/api`

**Step 3: Implement minimum client**

Use environment configuration, a replaceable HTTP transport, secure token storage, and typed request/response models generated or maintained from the OpenAPI contract.

**Step 4: Verify GREEN**

Run the same Flutter tests; expect all pass.

**Step 5: Commit**

```bash
git add mobile
git commit -m "feat: scaffold Flutter app and API client"
```

### Task 13: Flutter student vertical slice

**Files:**
- Create/modify feature files under `mobile/lib/features/`
- Create: `mobile/lib/widgets/source_citation.dart`
- Create: `mobile/lib/widgets/audio_player.dart`
- Test: `mobile/test/features/lesson_flow_test.dart`
- Test: `mobile/test/features/tutor_flow_test.dart`
- Test: `mobile/test/features/quiz_flow_test.dart`

**Step 1: Write failing widget tests**

Cover login, lesson list, lesson detail, language switch, image selection, grounded tutor result with page citation, refusal state, quiz setup, timer display, two-play indicator, submit, and result screen.

**Step 2: Verify RED**

Run: `cd mobile && flutter test test/features`

**Step 3: Implement the screens against a fake API client**

Keep UI state separate from transport. Ensure Android emulator base URL is supplied externally and no host IP appears in Dart source.

**Step 4: Verify GREEN**

Run: `cd mobile && flutter test`

Expected: all Flutter tests pass.

**Step 5: Commit**

```bash
git add mobile
git commit -m "feat: add Flutter learning tutor and quiz flows"
```

### Task 14: Evaluation, security checks, and final documentation

**Files:**
- Create: `evaluation/unit-1-2-queries.json`
- Create: `backend/src/english7/evaluation.py`
- Create: `scripts/check-no-secrets.sh`
- Create: `scripts/check-no-hardcoded-config.sh`
- Create: `docs/setup-linux.md`
- Create: `docs/setup-windows.md`
- Create: `docs/android-studio.md`
- Modify: `README.md`
- Test: `backend/tests/test_evaluation.py`

**Step 1: Add failing acceptance checks**

The evaluation runner must report retrieval accuracy, citation correctness, grounded answer success, and correct out-of-scope refusal. Configuration check scans source for forbidden secret patterns, absolute developer paths, direct OpenRouter calls outside the provider, and direct database access from mobile.

**Step 2: Verify RED**

Run: `bash scripts/check-no-secrets.sh && bash scripts/check-no-hardcoded-config.sh`

Expected: FAIL until scripts/config cleanup are complete.

**Step 3: Add documentation and fix violations**

Document Docker startup, migrations, seed import, optional NVIDIA profile, Android Studio setup, emulator API configuration, backups, and troubleshooting.

**Step 4: Full verification**

Run:

```bash
docker compose --env-file .env.example config --quiet
docker compose up -d sqlserver neo4j minio minio-init
docker compose run --rm api alembic upgrade head
docker compose run --rm api pytest -q
cd mobile && flutter analyze && flutter test
bash scripts/check-no-secrets.sh
bash scripts/check-no-hardcoded-config.sh
```

Expected: all commands exit 0, no test failures, no analysis errors, and no hardcoded configuration violations.

**Step 5: Commit**

```bash
git add evaluation backend scripts docs README.md
git commit -m "docs: add evaluation and cross-platform setup"
```

## Acceptance checklist

- API is versioned under `/api/v1` and documented through OpenAPI.
- Flutter never accesses SQL Server, Neo4j, MinIO, or OpenRouter directly.
- No secret, developer path, model choice, threshold, host, or business policy is hardcoded.
- Default Docker Compose works on Linux and Windows without NVIDIA.
- Optional GPU ingestion can run on the RTX 2050 host.
- Only verified Unit 1–2 fragments enter retrieval.
- Tutor refuses answers without valid SGK evidence.
- Every returned answer and generated question has valid source IDs.
- Audio in tests can be started no more than twice and the count survives resume.
- Quiz time and difficulty are policy-driven.
- Backend and Flutter automated tests pass.
