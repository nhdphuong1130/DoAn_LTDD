# Flashcard Vocabulary Pronunciation with VieNeu-TTS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement on-demand vocabulary pronunciation using VieNeu-TTS with server-side caching for flashcard review and speaking practice.

**Architecture:** A FastAPI endpoint `GET /api/v1/flashcards/cards/{card_id}/audio` resolves audio bytes by checking a local disk cache (`.cache/vocab_audio/{hash}.wav`), falling back to synthesizing via `LocalSpeechRuntime` (VieNeu-TTS) on cache miss. The Flutter client adds `loadCardAudio` to `LearningApi`, embedding a speaker button in `ReviewScreen` and updating "Nghe mẫu tiếng Anh" in `SpeakingScreen`.

**Tech Stack:** Python 3.12, FastAPI, VieNeu-TTS (via speech runtime), Flutter / Dart, `flutter_test`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-30-flashcard-vieneu-tts-pronunciation-design.md`

## Global Constraints
- Grounding: Preserve textbook citations `[Unit X, Page Y]` and ontology linkage.
- Architecture: Presentation (routers) and infrastructure depend on service interfaces, business logic lives in service classes.
- Error Handling: Speech service downtime must not block flashcard reviewing or grading.
- Quality Gates: Must pass `make test` and `make analyze` with zero failures and zero lint warnings.

---

### Task 1: Backend Audio Cache & Vocabulary Audio Service

**Files:**
- Create: `backend/src/english7/modules/flashcards/audio_cache.py`
- Modify: `backend/src/english7/modules/flashcards/service.py`
- Modify: `backend/src/english7/modules/flashcards/router.py`
- Modify: `backend/src/english7/core/settings.py`
- Test: `backend/tests/modules/flashcards/test_audio.py`

**Interfaces:**
- Consumes: `LocalSpeechRuntime.synthesize(text: str, voice_id: str) -> bytes`, `FlashcardRepository.card(card_id: UUID)`
- Produces: `FlashcardService.card_audio(user_id: UUID, card_id: UUID) -> bytes`
- Produces: Endpoint `GET /api/v1/flashcards/cards/{card_id}/audio`

- [x] **Step 1: Write the failing test for vocabulary audio service and caching**

```python
# backend/tests/modules/flashcards/test_audio.py
import pytest
from pathlib import Path
from uuid import uuid4
from english7.api.errors import ApplicationError
from english7.modules.flashcards.audio_cache import VocabAudioCache

class FakeSpeechRuntime:
    def __init__(self):
        self.calls = []
    def synthesize(self, text: str, voice_id: str) -> bytes:
        self.calls.append((text, voice_id))
        return b"RIFFfakeaudioWAVEfmt "

def test_cache_miss_synthesizes_and_caches(tmp_path: Path):
    runtime = FakeSpeechRuntime()
    cache = VocabAudioCache(cache_dir=tmp_path, runtime=runtime)
    audio = cache.get_or_synthesize("community", "Mai Anh")
    assert audio == b"RIFFfakeaudioWAVEfmt "
    assert len(runtime.calls) == 1
    
    # Second call should hit disk cache without re-synthesizing
    cached_audio = cache.get_or_synthesize("community", "Mai Anh")
    assert cached_audio == b"RIFFfakeaudioWAVEfmt "
    assert len(runtime.calls) == 1
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/modules/flashcards/test_audio.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'english7.modules.flashcards.audio_cache'`

- [x] **Step 3: Implement `VocabAudioCache` and wire into `FlashcardService` and `router.py`**

Create `backend/src/english7/modules/flashcards/audio_cache.py`:
```python
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Protocol

class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str, voice_id: str) -> bytes: ...

class VocabAudioCache:
    def __init__(self, cache_dir: Path, runtime: SpeechSynthesizer, default_voice: str = "Mai Anh"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.runtime = runtime
        self.default_voice = default_voice

    def _file_path(self, word: str, voice_id: str) -> Path:
        normalized = word.strip().casefold()
        key = hashlib.sha256(f"{normalized}:{voice_id}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.wav"

    def get_or_synthesize(self, word: str, voice_id: str | None = None) -> bytes:
        voice = voice_id or self.default_voice
        target = self._file_path(word, voice)
        if target.is_file() and target.stat().st_size > 0:
            return target.read_bytes()
        audio = self.runtime.synthesize(word.strip(), voice)
        if audio:
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, delete=False) as tmp:
                tmp.write(audio)
                tmp_path = Path(tmp.name)
            os.replace(tmp_path, target)
        return audio
```

In `FlashcardService` (`backend/src/english7/modules/flashcards/service.py`), add:
```python
def card_audio(self, user_id: UUID, card_id: UUID) -> bytes:
    card = self.get_card(user_id, card_id)
    if self.audio_cache is None:
        raise ApplicationError("speech_unavailable", "Audio service is not configured", 503)
    return self.audio_cache.get_or_synthesize(card.word)
```

In `FlashcardRouter` (`backend/src/english7/modules/flashcards/router.py`), add:
```python
@router.get('/cards/{card_id}/audio')
def card_audio(card_id: UUID, user: Student, service: Service) -> Response:
    audio_bytes = service.card_audio(user.id, card_id)
    return Response(content=audio_bytes, media_type='audio/wav', headers={'Cache-Control': 'public, max-age=86400'})
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/modules/flashcards/test_audio.py -v`
Expected: PASS

- [x] **Step 5: Write API integration test in `backend/tests/api/test_learning.py`**

Test `client.get(f'/api/v1/flashcards/cards/{card_id}/audio', headers=student_headers)` returning `200` with `audio/wav`.

- [x] **Step 6: Commit backend changes**

```bash
git add backend/src/english7/modules/flashcards/ backend/tests/
git commit -m "feat(backend): add vocab audio caching and card audio endpoint"
```

---

### Task 2: Mobile Contract & API Client Updates

**Files:**
- Modify: `mobile/lib/app/learning_api.dart`
- Modify: `mobile/lib/app/api_learning.dart`
- Modify: `mobile/test/features/support/fake_learning.dart`
- Test: `mobile/test/app/api_learning_test.dart`

**Interfaces:**
- Produces: `LearningApi.loadCardAudio(String cardId) -> Future<Uint8List>`

- [x] **Step 1: Write failing test in `mobile/test/app/api_learning_test.dart`**

```dart
test('loadCardAudio fetches audio bytes for card id', () async {
  when(() => client.audioBytes('/api/v1/flashcards/cards/card-123/audio'))
      .thenAnswer((_) async => Uint8List.fromList([1, 2, 3]));
  final bytes = await api.loadCardAudio('card-123');
  expect(bytes, [1, 2, 3]);
});
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd mobile && flutter test test/app/api_learning_test.dart`
Expected: FAIL with `The method 'loadCardAudio' isn't defined`

- [x] **Step 3: Implement `loadCardAudio` in `LearningApi` and `ApiLearning`**

In `mobile/lib/app/learning_api.dart`:
```dart
Future<Uint8List> loadCardAudio(String cardId);
```

In `mobile/lib/app/api_learning.dart`:
```dart
@override
Future<Uint8List> loadCardAudio(String cardId) =>
    learningClient.audioBytes('/api/v1/flashcards/cards/$cardId/audio');
```

Update `FakeLearningApi` in `mobile/test/features/support/fake_learning.dart`:
```dart
@override
Future<Uint8List> loadCardAudio(String cardId) async => Uint8List.fromList([1, 2, 3]);
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd mobile && flutter test test/app/api_learning_test.dart`
Expected: PASS

- [x] **Step 5: Commit mobile API client changes**

```bash
git add mobile/lib/app/ mobile/test/
git commit -m "feat(mobile): add loadCardAudio to LearningApi contract"
```

---

### Task 3: Mobile Flashcard Review Screen Audio Pronunciation

**Files:**
- Modify: `mobile/lib/features/flashcards/review_screen.dart`
- Test: `mobile/test/features/learning_flow_test.dart`

**Interfaces:**
- Consumes: `LearningApi.loadCardAudio(String cardId)`
- Produces: Speaker button `Icons.volume_up` on revealed flashcard to hear pronunciation.

- [x] **Step 1: Write failing widget test in `mobile/test/features/learning_flow_test.dart`**

```dart
testWidgets('review screen shows audio speaker button on revealed card and plays audio', (tester) async {
  // Setup FakeLearningApi with card
  // Pump ReviewScreen
  // Tap 'Xem đáp án'
  // Verify Icons.volume_up is found
  // Tap Icons.volume_up and verify loadCardAudio was invoked
});
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd mobile && flutter test test/features/learning_flow_test.dart`
Expected: FAIL (no `Icons.volume_up` found)

- [x] **Step 3: Implement speaker button and audio playback in `ReviewScreen`**

In `mobile/lib/features/flashcards/review_screen.dart`:
- Add `bool _playingAudio = false;` state.
- In revealed section, next to `card.word`, add an `IconButton(icon: Icon(Icons.volume_up))` with loading state.
- Implement `_playAudio(String cardId)` to call `widget.api.loadCardAudio(cardId)` and play through `SpeechRecorder` or native audio player, catching errors with a SnackBar notification.

- [x] **Step 4: Run test to verify it passes**

Run: `cd mobile && flutter test test/features/learning_flow_test.dart`
Expected: PASS

- [x] **Step 5: Commit review screen changes**

```bash
git add mobile/lib/features/flashcards/review_screen.dart mobile/test/
git commit -m "feat(mobile): add pronunciation audio playback to flashcard review screen"
```

---

### Task 4: Mobile Speaking Screen Sample Audio Integration

**Files:**
- Modify: `mobile/lib/features/speaking/speaking_screen.dart`
- Test: `mobile/test/features/learning_flow_test.dart`

**Interfaces:**
- Consumes: `LearningApi.loadCardAudio(String cardId)`
- Produces: Always-enabled "Nghe mẫu tiếng Anh" button playing vocabulary pronunciation via VieNeu-TTS.

- [x] **Step 1: Write failing test in `mobile/test/features/learning_flow_test.dart`**

Verify that even when `card.audioUrl == null`, "Nghe mẫu tiếng Anh" button is enabled, and tapping it calls `loadCardAudio(card.id)`.

- [x] **Step 2: Run test to verify it fails**

Run: `cd mobile && flutter test test/features/learning_flow_test.dart`
Expected: FAIL with missing button or "Chưa có audio..." text present.

- [x] **Step 3: Update `SpeakingScreen` to call `loadCardAudio(card.id)`**

In `mobile/lib/features/speaking/speaking_screen.dart`:
- Replace `if (card.audioUrl == null) ... else ...` with an unconditional `OutlinedButton` titled `'Nghe mẫu tiếng Anh'`.
- Wire `onPressed` to `() => _run(() => _playResponse(widget.api.loadCardAudio(card.id)))`.

- [x] **Step 4: Run test to verify it passes**

Run: `cd mobile && flutter test test/features/learning_flow_test.dart`
Expected: PASS

- [x] **Step 5: Commit speaking screen changes**

```bash
git add mobile/lib/features/speaking/speaking_screen.dart mobile/test/
git commit -m "feat(mobile): enable sample pronunciation audio via VieNeu-TTS in speaking screen"
```

---

### Task 5: Full Project Verification & Quality Gates

**Files:**
- All modified files

- [x] **Step 1: Run full backend test suite**

Run: `cd backend && pytest`
Expected: All tests PASS.

- [x] **Step 2: Run full mobile test suite and analyzer**

Run: `cd mobile && flutter test && flutter analyze`
Expected: Zero test failures, zero lint issues.

- [x] **Step 3: Run root make check targets**

Run: `make test && make analyze`
Expected: PASS.
