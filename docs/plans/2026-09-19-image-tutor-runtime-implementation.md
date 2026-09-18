# Image Tutor Runtime Integration Implementation Plan

**Goal:** Add an end-to-end, owner-scoped image upload flow that extracts a
student question with DocLayout-YOLO and PaddleOCR, then answers only from
verified Unit 1–2 evidence through the existing Tutor API.

**Architecture:** Store upload metadata in SQL Server and image bytes in MinIO,
process queued uploads through provider-neutral worker services, and pass only
sanitized OCR text into hierarchical graph-vector retrieval. Flutter uploads
multipart bytes, polls the upload state, and sends the resulting upload ID with
the typed Tutor question.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy/Alembic, SQL Server, MinIO,
DocLayout-YOLO, PaddleOCR, pytest, Flutter/Dart, Docker Compose.

---

### Task 1: Image upload persistence and configuration

**Files:**
- Modify: `backend/src/english7/core/settings.py`
- Modify: `backend/src/english7/db/models.py`
- Create: `backend/alembic/versions/0003_student_image_uploads.py`
- Create: `backend/src/english7/modules/image_uploads/__init__.py`
- Create: `backend/src/english7/modules/image_uploads/domain.py`
- Create: `backend/src/english7/modules/image_uploads/repository.py`
- Create: `backend/tests/modules/image_uploads/test_repository.py`
- Modify: `.env.example`
- Modify: `compose.yaml`

**Step 1: Write the failing repository test**

Create a repository test that saves a queued upload with owner ID, generated
object key, checksum, media type, size, and expiry, then proves another owner
cannot retrieve it. Add state-transition assertions for `processing`, `ready`,
and `failed`.

```python
created = repository.create(owner_id, "image/png", 123, checksum, expires_at)
assert repository.get_for_owner(created.id, owner_id).status is UploadStatus.QUEUED
assert repository.get_for_owner(created.id, uuid4()) is None
repository.mark_ready(created.id, "recognized question", 0.91)
assert repository.get_for_owner(created.id, owner_id).ocr_text == "recognized question"
```

**Step 2: Verify RED**

Run:

```bash
docker compose --env-file .env.example run --rm api \
  pytest tests/modules/image_uploads/test_repository.py -q
```

Expected: FAIL because the upload model and repository do not exist.

**Step 3: Implement the domain, model, migration, and repository**

Add `ImageUploadStatus` with `queued`, `processing`, `ready`, and `failed`.
Add `StudentImageUpload` fields for owner, object key, checksum, media type,
size, OCR text/confidence, failure code, expiry, and completion time. Repository
queries must always include owner ID for student-facing reads.

Add configuration fields:

```python
image_upload_prefix: str | None = None
image_upload_retention_minutes: int | None = None
image_upload_allowed_types: str | None = None
ocr_languages: str | None = None
ocr_minimum_confidence: float | None = None
```

**Step 4: Verify GREEN and migration**

Run the targeted test and `alembic upgrade head`; expect PASS.

**Step 5: Commit**

```bash
git add backend .env.example compose.yaml
git commit -m "feat: persist owner-scoped image uploads"
```

### Task 2: Validated upload API

**Files:**
- Create: `backend/src/english7/modules/image_uploads/validation.py`
- Create: `backend/src/english7/modules/image_uploads/service.py`
- Create: `backend/src/english7/modules/image_uploads/router.py`
- Modify: `backend/src/english7/api/router.py`
- Modify: `backend/src/english7/modules/media/storage.py`
- Modify: `backend/pyproject.toml`
- Create: `backend/tests/modules/image_uploads/test_service.py`
- Create: `backend/tests/api/test_image_uploads.py`

**Step 1: Write failing service and API tests**

Cover valid PNG/JPEG/WebP magic bytes, MIME spoofing, configured size limit,
server-generated object keys, queued response, owner-only status reads, expired
uploads, and unsupported types. Use `UploadFile` only at the router boundary.

```python
response = client.post(
    "/api/v1/tutor/images",
    files={"image": ("exercise.png", PNG_BYTES, "image/png")},
)
assert response.status_code == 202
assert response.json()["status"] == "queued"
```

**Step 2: Verify RED**

Run both new test files; expect 404/import failures for the missing route.

**Step 3: Implement minimal API behavior**

Use `python-multipart` for multipart parsing. Read at most
`upload_max_bytes + 1`, validate image signatures independently of the client
MIME header, hash bytes, create the record, save under a generated object key,
and return only upload ID/status. Add:

- `POST /api/v1/tutor/images` -> HTTP 202
- `GET /api/v1/tutor/images/{upload_id}` -> owner-scoped status

**Step 4: Verify GREEN**

Run targeted tests and the full backend suite.

**Step 5: Commit**

```bash
git add backend
git commit -m "feat: add validated tutor image upload API"
```

### Task 3: DocLayout-YOLO and PaddleOCR processing worker

**Files:**
- Create: `backend/src/english7/modules/image_uploads/processor.py`
- Create: `backend/src/english7/modules/ingestion/device.py`
- Create: `backend/src/english7/modules/ingestion/providers.py`
- Modify: `backend/src/english7/worker.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/Dockerfile`
- Modify: `compose.yaml`
- Create: `backend/tests/modules/image_uploads/test_processor.py`
- Create: `backend/tests/modules/ingestion/test_device.py`

**Step 1: Write failing processor/device tests**

Test `auto` selecting CUDA only when reported available, explicit CPU behavior,
OCR region ordering, confidence filtering, whitespace normalization, ready state,
no-text failure, and provider exception failure. Inject detector/OCR functions;
unit tests must not load model weights.

**Step 2: Verify RED**

Run the two test files; expect missing imports.

**Step 3: Implement adapters and worker dispatch**

Create lazy provider factories. `auto` resolves at worker startup. Download the
MinIO object, detect regions, OCR in reading order, retain text at or above the
configured threshold, and update the record. Keep heavy model packages in a
`vision` optional dependency and install them only in the worker vision target.

The worker claims one queued upload atomically per poll so CPU and GPU workers
cannot process the same upload.

**Step 4: Verify GREEN**

Run unit tests, CPU Compose config, and GPU Compose config.

**Step 5: Commit**

```bash
git add backend compose.yaml
git commit -m "feat: process tutor images with layout OCR workers"
```

### Task 4: Tutor upload query integration and runtime composition

**Files:**
- Modify: `backend/src/english7/modules/tutor/router.py`
- Modify: `backend/src/english7/modules/tutor/service.py`
- Create: `backend/src/english7/bootstrap.py`
- Modify: `backend/src/english7/main.py`
- Modify: `backend/tests/api/test_tutor.py`
- Create: `backend/tests/modules/tutor/test_image_question.py`
- Create: `backend/tests/test_bootstrap.py`

**Step 1: Write failing Tutor tests**

Test that an owned ready upload augments the query, unready/expired/foreign IDs
are rejected, OCR alone can form the query, raw OCR is not passed as evidence,
and Tutor still refuses when retrieval returns no verified fragments.

```python
answer = service.ask(
    question="Giải bài này",
    language=Language.VIETNAMESE,
    user_id=student_id,
    upload_id=upload.id,
)
assert retriever.queries == ["Giải bài này\nrecognized exercise text"]
```

**Step 2: Verify RED**

Run targeted Tutor/bootstrap tests; expect signature and configuration failures.

**Step 3: Implement query augmentation and dependency composition**

Extend `AskTutorRequest` with optional `upload_id`. Resolve OCR by owner, build a
bounded normalized query, then reuse the existing retrieval/provider/citation
validation. In FastAPI lifespan, construct SQL repositories, Neo4j retrieval,
MinIO storage, OpenRouter, Tutor, Quiz, and upload services from Settings. Fail
with a clear startup error when a required runtime setting is absent; tests may
override dependencies as before.

**Step 4: Verify GREEN**

Run targeted tests, all backend tests, and API health through Compose.

**Step 5: Commit**

```bash
git add backend
git commit -m "feat: connect image OCR to grounded tutor runtime"
```

### Task 5: Flutter multipart upload and polling

**Files:**
- Modify: `mobile/lib/api/http_transport.dart`
- Modify: `mobile/lib/api/api_client.dart`
- Modify: `mobile/lib/app/student_api.dart`
- Modify: `mobile/lib/app/api_student_api.dart`
- Modify: `mobile/lib/features/tutor/tutor_screen.dart`
- Modify: `mobile/test/api/api_client_test.dart`
- Modify: `mobile/test/features/tutor_flow_test.dart`
- Modify: `mobile/test/features/support/fakes.dart`

**Step 1: Write failing Flutter tests**

Test multipart boundary/body/header construction, upload response parsing,
queued/processing polling, ready upload ID submission, processing failure, and
visible progress. Inject polling delay so widget tests use `Duration.zero`.

**Step 2: Verify RED**

Run:

```bash
cd mobile
flutter test test/api/api_client_test.dart test/features/tutor_flow_test.dart
```

Expected: compile/test failures because multipart and upload APIs are absent.

**Step 3: Implement minimal Flutter flow**

Read selected image bytes, send multipart with the bearer token, poll the status
endpoint with a bounded attempt count, then call Tutor with `upload_id` rather
than the local file path. Show upload/OCR/answer states and stable API errors.

**Step 4: Verify GREEN**

Run `dart format`, `flutter analyze`, and all Flutter tests.

**Step 5: Commit**

```bash
git add mobile
git commit -m "feat: upload tutor images from Flutter"
```

### Task 6: End-to-end verification and operations documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/setup-linux.md`
- Modify: `docs/setup-windows.md`
- Modify: `scripts/check-no-hardcoded-config.sh`
- Create: `backend/tests/integration/test_image_upload_flow.py`

**Step 1: Write the integration test**

Exercise authenticated upload, SQL persistence, MinIO object creation, fake
worker processing, ready status, Tutor query augmentation, and closed-world
refusal without approved evidence.

**Step 2: Verify RED, then implement only missing composition fixes**

Run the integration test against Compose and confirm it fails before any final
glue change. Add only the wiring required for the test to pass.

**Step 3: Document CPU/GPU operation**

Document model cache, first-start model download, `auto/cpu/cuda`, Windows CPU
limits, retention cleanup, and the opt-in real-model smoke test. Do not include
developer-specific absolute paths or credentials.

**Step 4: Final verification**

Run:

```bash
docker compose --env-file .env.example run --rm api alembic upgrade head
docker compose --env-file .env.example run --rm api pytest -q
cd mobile && dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
cd ..
./scripts/check-no-secrets.sh
./scripts/check-no-hardcoded-config.sh
docker compose --env-file .env.example config --quiet
docker compose --env-file .env.example --profile gpu config --quiet
git diff --check
```

**Step 5: Commit**

```bash
git add README.md docs scripts backend/tests/integration
git commit -m "docs: add image tutor runtime operations"
```

