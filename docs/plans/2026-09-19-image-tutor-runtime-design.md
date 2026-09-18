# Image Tutor Runtime Integration Design

**Date:** 2026-09-19  
**Status:** Approved  
**Scope:** Production integration for student image upload, DocLayout-YOLO,
PaddleOCR, grounded retrieval, and OpenRouter.

## Objectives

- Let a Flutter student upload a JPEG, PNG, or WebP exercise image.
- Use DocLayout-YOLO for layout detection and PaddleOCR for Vietnamese/English
  recognition.
- Use OCR text only as a query signal; it must never become verified knowledge.
- Answer only when approved Unit 1–2 textbook fragments support the response.
- Run with CUDA on the Linux RTX 2050 and fall back to CPU on Windows or on
  hosts without a compatible GPU.
- Keep model identifiers, limits, thresholds, retention, and provider settings
  outside application code.

## Architecture and Data Flow

Verified textbook ingestion and student image processing share layout and OCR
provider interfaces but have different trust boundaries.

The textbook worker renders PDF pages, detects text, image, and exercise regions,
and performs OCR. Extracted fragments remain pending until an administrator
reviews them. Only approved fragments are synchronized to the Neo4j hierarchy
and vector index.

For a student image, Flutter uploads multipart data to
`POST /api/v1/tutor/images`. The API validates ownership, content type, actual
image bytes, and configured size limits, stores the object in MinIO, and queues
processing. A worker uses DocLayout-YOLO and PaddleOCR and saves an expiring OCR
result. The OCR text is untrusted and may only augment the student's question.
It is never inserted into the verified knowledge graph.

Flutter polls `GET /api/v1/tutor/images/{upload_id}` until the upload becomes
`ready` or `failed`, then submits `question`, `language`, and `upload_id` to
`POST /api/v1/tutor/ask`. The backend combines the typed question and OCR query,
runs hierarchical graph-vector retrieval, and sends only approved SGK evidence
to OpenRouter. Returned citations are checked against the supplied evidence.
Missing evidence causes a stable refusal.

## Runtime Providers

DocLayout-YOLO and PaddleOCR are loaded behind existing layout and OCR contracts.
`INGESTION_DEVICE=auto` selects CUDA when available and otherwise selects CPU.
Explicit `cpu` and `cuda` modes remain available for repeatable deployments.
The model identifier, layout confidence, OCR languages, minimum OCR confidence,
upload size, retention period, and worker behavior are configuration values.

Heavy model dependencies live in the worker image. The FastAPI image stays
small and does not load CUDA libraries. Unit tests use deterministic provider
fakes; real model loading belongs to an opt-in integration test and the GPU
Compose profile.

## Persistence and Ownership

Each upload records its owner, object key, checksum, detected media type,
status, sanitized OCR text, confidence, failure code, creation time, completion
time, and expiry time. Status transitions are `queued -> processing -> ready`
or `queued/processing -> failed`.

Only the owner or an administrator may inspect an upload. Tutor requests reject
unknown, expired, unfinished, or foreign upload identifiers. Object keys are
server-generated and never accepted from Flutter. A scheduled cleanup job
deletes expired MinIO objects and database records according to the configured
retention policy.

## Error Contract

The API uses the existing standard error envelope and stable codes:

- `unsupported_image_type`
- `upload_too_large`
- `image_processing_failed`
- `image_text_not_found`
- `image_upload_not_ready`
- `image_upload_forbidden`
- `out_of_scope`
- `invalid_ai_citations`
- `ai_provider_failed`

Provider exceptions are logged with the trace ID but are not returned to the
student. OCR text and credentials are excluded from routine logs.

## Testing Strategy

Backend tests cover signature-based image validation, configured limits,
ownership, state transitions, expiration, OCR with no usable text, CPU fallback,
query augmentation, closed-world refusal, and citation validation. Integration
tests cover SQL Server persistence, MinIO object storage, worker processing, and
an opt-in real-model smoke test.

Flutter tests cover multipart upload, polling states, retryable errors, language
selection, and submitting a ready `upload_id` to Tutor. Existing backend,
Flutter, configuration, secret, CPU Compose, and GPU Compose checks remain
mandatory before completion.

