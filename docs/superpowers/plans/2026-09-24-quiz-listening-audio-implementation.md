# Quiz Listening Audio Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow students to select their quiz format (Listening, Reading, Mixed), extract authentic textbook audio tracks for listening questions, and connect mobile audio playback to the backend audio stream with limited play constraints.

**Architecture:** 
1. Backend updates: enhance quiz options and generation requests to accept `mode` (`listening`, `reading`, `mixed`), update `GroundedQuestionGenerator` to query textbook `Activity` records linked to `AudioTrack` and produce questions with `audio_url` (`/api/v1/media/audio/{track_number}`).
2. Mobile API: update `QuizSetup`, `QuizOptions`, and `QuizSession` contracts to convey `mode`, `audioUrl`, and `audioTitle`.
3. Mobile UI: introduce exam mode choice chips in `QuizScreen` and connect `LimitedAudioPlayer` to `NativeAudioPlayer` so audio actually streams when present, while cleanly hiding the player for reading-only quizzes.

**Tech Stack:** FastAPI, SQLAlchemy, Flutter, Dart, NativeAudioPlayer, MinIO.

**Spec:** `docs/superpowers/specs/2026-09-24-quiz-listening-audio-design.md`

## Global Constraints
- Grounding: Audio tracks and listening activities MUST be authentic Global Success textbook content.
- Audio limits: Max 2 plays, no seeking, atomic decrement.
- Zero warnings on `make analyze`, all tests pass on `make test`.

---

### Task 1: Backend Quiz Models, Generation & API Updates

**Files:**
- Modify: `backend/src/english7/modules/quizzes/domain.py`
- Modify: `backend/src/english7/modules/quizzes/router.py`
- Modify: `backend/src/english7/modules/quizzes/service.py`
- Modify: `backend/src/english7/bootstrap.py`
- Test: `backend/tests/modules/quizzes/test_quiz_service.py` or new test file `backend/tests/modules/quizzes/test_quiz_modes.py`

**Interfaces:**
- Produces: `QuizOptionsResponse.modes: list[str]`, `GenerateQuizRequest.mode: str`, `QuizResponse.audio_url: str | None`, `QuizResponse.audio_title: str | None`.

- [ ] **Step 1: Write failing tests for quiz modes and audio URL in backend**
- [ ] **Step 2: Run pytest to confirm tests fail**
- [ ] **Step 3: Update `domain.py`, `router.py`, `service.py`, and `GroundedQuestionGenerator` in `bootstrap.py`**
- [ ] **Step 4: Run pytest to confirm all tests pass**
- [ ] **Step 5: Commit changes**

---

### Task 2: Mobile Student API & Model Updates

**Files:**
- Modify: `mobile/lib/app/student_api.dart`
- Modify: `mobile/lib/app/api_student_api.dart`
- Modify: `mobile/test/features/support/fakes.dart`
- Test: `mobile/test/app/api_student_api_test.dart`

**Interfaces:**
- Consumes: Backend `QuizOptionsResponse.modes`, `QuizResponse.audio_url`, `QuizResponse.audio_title`.
- Produces: `QuizSetup(duration, difficulty, mode)`, `QuizSession(id, durationMinutes, difficulty, questions, audioUrl, audioTitle)`.

- [ ] **Step 1: Write failing test in `mobile/test/app/api_student_api_test.dart` for quiz modes and audio fields**
- [ ] **Step 2: Run flutter test to confirm test fails**
- [ ] **Step 3: Update `student_api.dart`, `api_student_api.dart`, and test fakes**
- [ ] **Step 4: Run flutter test to confirm tests pass**
- [ ] **Step 5: Commit changes**

---

### Task 3: Mobile UI Quiz Mode Selector & Real Audio Playback

**Files:**
- Modify: `mobile/lib/widgets/audio_player.dart`
- Modify: `mobile/lib/features/quizzes/quiz_screen.dart`
- Test: `mobile/test/features/quiz_flow_test.dart`

**Interfaces:**
- Consumes: `QuizSession.audioUrl`, `NativeAudioPlayer.play(url)`.

- [ ] **Step 1: Write failing widget tests in `quiz_flow_test.dart` for mode selection, audio player visibility, and audio play trigger**
- [ ] **Step 2: Run flutter test to confirm tests fail**
- [ ] **Step 3: Update `quiz_screen.dart` and `audio_player.dart` to support mode chips and connect `onPlay` to `NativeAudioPlayer.play(resolvedUrl)`**
- [ ] **Step 4: Run flutter test to confirm all mobile tests pass**
- [ ] **Step 5: Commit changes**

---

### Task 4: Full System Verification

- [ ] **Step 1: Run `make test` (backend + mobile tests)**
- [ ] **Step 2: Run `make analyze`**
- [ ] **Step 3: Hot reload/restart mobile app on Android emulator and verify real quiz flow**
