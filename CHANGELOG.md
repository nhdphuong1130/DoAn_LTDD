# Changelog

All notable changes to the English 7 Grounded Learning Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dedicated "Ôn luyện nói cả câu" (Sentence Speaking Practice) session for each unit with Duolingo-style step-by-step progress, auto-advance on >=80% match, word-by-word evaluation chips, and skip button ("Bỏ qua") for difficult sentences.
- Private/published flashcard decks, recall-based review schedules, difficult-word flags and verified textbook vocabulary seeding with real Unit/page citations.
- Optional free CPU speech practice: bounded Android WAV recording, transcript/word comparison (not a pronunciation grade), selectable VieNeu Vietnamese feedback voices and persistent owner-scoped history.
- Learning navigation and vocabulary/speaking progress summaries; additive migration and `make` commands for optional speech setup, startup and tests.
- Standardized repository structure aligned with OLP 2026 open-source standards (`.agents/`, `.github/`, `infra/`, `scripts/`, `docs/`, `Makefile`).
- Top-level `Makefile` orchestrating Docker environment, backend tests, Flutter analysis, and security audits.
- Quality and safety checklists for Clean Architecture, open-source readiness, and AI agents.

### Changed
- Removed English example sentence display from flashcard back card and deck card list, keeping flashcards focused strictly on English word + phonetic on the front, and Vietnamese meaning on the back.
- Load retrieval embeddings lazily into the persistent configured cache so model downloads cannot block login or flashcard startup.
- Persist quiz submissions and graded answers atomically, scope progress to the authenticated student, and make submission retries idempotent. Replace the placeholder progress tab with totals, accuracy, submission history, refresh, and error recovery.
- Added `make run` with backend readiness checks, connected emulator detection and published API port forwarding; `make up` starts core services, while `make up-full` includes the OCR worker.
- Increased vision dependency download timeout to 300 seconds and added launcher regression tests.
- Filtered unsuitable fragments (images, lists, arrows) and cleaned prompts in quiz generator.
- Improved quiz question generation with targeted AI True/False/Not given answers and single-batch requests.

## [0.1.0] - 2026-09-21

### Added
- **Semester 2 Curriculum & Audio Player**:
  - Full authentic lesson content for Units 7 to 12 and Review 3, 4 based on Tiếng Anh 7 Global Success.
  - Multi-source audio streaming endpoint (`/api/v1/media/audio/{track}`) with MinIO object storage and local fallback.
  - Timed quiz generation and submission workflow with question bank queries.
- **Neo4j Pedagogical GraphRAG & Vector Search**:
  - Dual vector indexing for `SourceFragment` and `KnowledgeConcept` using local FastEmbed (`bge-small-en-v1.5`, 384d).
  - Pedagogical ontology entities: `Topic`, `GrammarRule`, `Vocabulary`, and `PronunciationSound`.
  - Reciprocal Rank Fusion (RRF) and weighted graph search across curriculum relationships (`TEACHES`, `EXPLAINS`, `PRACTICES`).
- **Student Personal Profile**:
  - Personal profile endpoints (`GET /api/v1/auth/profile`, `PATCH /api/v1/auth/profile`, `POST /api/v1/auth/change-password`).
  - Mobile Flutter profile tab with student avatar, grade, school, date of birth, bio editing, and password update.
  - Session auto-restore and token persistence via Flutter secure storage.
- **Evidence-First Adaptive Knowledge Graph**:
  - Versioned graph builds with isolated label namespaces and atomic promotion.
  - Pre-flight validation verifying embedding dimensions, orphan endpoints, and index readiness.
