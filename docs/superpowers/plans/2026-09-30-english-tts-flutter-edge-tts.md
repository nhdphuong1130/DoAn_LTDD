# English TTS (flutter_tts & edge-tts) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement authentic English pronunciation using `flutter_tts` on mobile (native offline English TTS) and replace `VieNeu-TTS` with `edge-tts` on the backend Docker runtime.

**Architecture:** Mobile uses native Google TTS / iOS TTS (`flutter_tts`) configured for British English (`en-GB`) with graceful fallback to backend `loadCardAudio`. Backend `speech-runtime` replaces Vietnamese `VieNeu-TTS` with `edge-tts` generating high-quality neural English audio files cached in `VocabAudioCache`.

**Tech Stack:** Flutter (`flutter_tts: ^4.2.2`, Dart 3.13+), Python 3.12 (FastAPI, `edge-tts`, `faster-whisper`), Docker Compose.

**Spec:** [docs/superpowers/specs/2026-09-30-english-tts-flutter-edge-tts-design.md](file:///home/nguyenphuong/Documents/DoAN_LTDD/docs/superpowers/specs/2026-09-30-english-tts-flutter-edge-tts-design.md)

## Global Constraints

- Never commit secrets, real API keys, credentials, or `.env` files.
- All commands runnable via root `Makefile` or standard CLI.
- Always run `make test` and `make analyze` before finalizing work.
- Mobile screens must communicate via injected services for testability.

---

### Task 1: Replace VieNeu-TTS with edge-tts in Speech Runtime

**Files:**
- Modify: `speech/requirements.txt`
- Modify: `speech/engine.py`
- Modify: `speech/test_app.py`

**Interfaces:**
- Consumes: `edge-tts` python library
- Produces: `LocalEngine.synthesize(text, voice_id) -> bytes` (audio bytes, e.g. MP3/WAV)
- Produces: `LocalEngine.voices() -> list[dict]` with English voices: `en-GB-SoniaNeural`, `en-GB-RyanNeural`, `en-US-JennyNeural`, `en-US-GuyNeural`

- [ ] **Step 1: Write the failing unit test for English voices**

In `speech/test_app.py`, update voice assertions to expect English neural voices:
```python
def test_voices_endpoint():
    # Expect English voices including en-GB-SoniaNeural
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest speech/test_app.py -q`
Expected: FAIL due to mismatch with old Vietnamese voices.

- [ ] **Step 3: Update speech dependencies and engine**

In `speech/requirements.txt`:
```
faster-whisper>=1.2.1
edge-tts>=6.1.19
soundfile>=0.12.1
av>=14.0.0
numpy>=1.26.0
```

In `speech/engine.py`:
Replace `Vieneu` with `edge_tts`:
```python
VOICE_IDS = ("en-GB-SoniaNeural", "en-GB-RyanNeural", "en-US-JennyNeural", "en-US-GuyNeural")

class LocalEngine:
    ...
    def synthesize(self, text, voice_id):
        import asyncio
        import edge_tts
        communicate = edge_tts.Communicate(text, voice_id)
        # Collect audio chunks
        chunks = []
        async def _run():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
        asyncio.run(_run())
        return b"".join(chunks)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest speech/test_app.py -q`
Expected: PASS

- [ ] **Step 5: Commit Task 1**

```bash
git add speech/
git commit -m "feat(speech): replace VieNeu-TTS with edge-tts for English speech synthesis"
```

---

### Task 2: Update Backend VocabAudioCache & Flashcard Service

**Files:**
- Modify: `backend/src/english7/modules/flashcards/audio_cache.py`
- Modify: `backend/tests/modules/flashcards/test_audio.py`
- Modify: `backend/tests/api/test_learning.py`

**Interfaces:**
- Consumes: `VocabAudioCache.default_voice`
- Produces: `GET /api/v1/flashcards/cards/{card_id}/audio` using `en-GB-SoniaNeural`

- [ ] **Step 1: Write failing test in test_audio.py**

Update test voice from `"Mai Anh"` to `"en-GB-SoniaNeural"`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/modules/flashcards/test_audio.py -q`
Expected: FAIL

- [ ] **Step 3: Update VocabAudioCache default voice**

In `backend/src/english7/modules/flashcards/audio_cache.py`:
```python
class VocabAudioCache:
    def __init__(self, cache_dir: Path, runtime: SpeechSynthesizer, default_voice: str = "en-GB-SoniaNeural"):
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/modules/flashcards/test_audio.py tests/api/test_learning.py -q`
Expected: PASS

- [ ] **Step 5: Commit Task 2**

```bash
git add backend/
git commit -m "feat(backend): configure en-GB-SoniaNeural default voice for VocabAudioCache"
```

---

### Task 3: Mobile TtsService (flutter_tts) Interface & Implementation

**Files:**
- Modify: `mobile/pubspec.yaml`
- Modify: `mobile/android/app/src/main/AndroidManifest.xml`
- Create: `mobile/lib/services/tts_service.dart`
- Create: `mobile/test/services/tts_service_test.dart`

**Interfaces:**
- Consumes: `flutter_tts` package
- Produces: `TtsService` interface (`speak(String text, {String language = 'en-GB'})`, `stop()`, `dispose()`)
- Produces: `NativeTtsService` and `FakeTtsService`

- [ ] **Step 1: Add flutter_tts dependency and Android query**

Add `flutter_tts: ^4.2.2` to `mobile/pubspec.yaml`.
Add `<queries><intent><action android:name="android.intent.action.TTS_SERVICE" /></intent></queries>` to `mobile/android/app/src/main/AndroidManifest.xml`.
Run `flutter pub get`.

- [ ] **Step 2: Write failing test for TtsService**

Create `mobile/test/services/tts_service_test.dart` asserting that `FakeTtsService` records spoken words and languages.

- [ ] **Step 3: Implement TtsService**

Create `mobile/lib/services/tts_service.dart`:
```dart
abstract interface class TtsService {
  Future<void> speak(String text, {String language = 'en-GB'});
  Future<void> stop();
  Future<void> dispose();
}

class NativeTtsService implements TtsService {
  ...
}

class FakeTtsService implements TtsService {
  ...
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd mobile && flutter test test/services/tts_service_test.dart`
Expected: PASS

- [ ] **Step 5: Commit Task 3**

```bash
git add mobile/
git commit -m "feat(mobile): add TtsService with flutter_tts and FakeTtsService"
```

---

### Task 4: Integrate TtsService into Flashcard & Speaking Screens

**Files:**
- Modify: `mobile/lib/features/flashcards/learning_screen.dart`
- Modify: `mobile/lib/features/flashcards/review_screen.dart`
- Modify: `mobile/lib/features/speaking/speaking_screen.dart`
- Modify: `mobile/test/features/learning_flow_test.dart`

**Interfaces:**
- Consumes: `TtsService` injected into screens
- Produces: Direct on-device pronunciation playback with graceful fallback to `api.loadCardAudio`

- [ ] **Step 1: Update learning_flow_test.dart to test TtsService invocation**

Write widget tests verifying that tapping `Nghe phát âm tiếng Anh` calls `ttsService.speak(card.word, language: 'en-GB')`, and when TTS errors, falls back to `api.loadCardAudio`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd mobile && flutter test test/features/learning_flow_test.dart`
Expected: FAIL

- [ ] **Step 3: Implement TtsService integration on screens**

In `DeckScreen`, `ReviewScreen`, and `SpeakingScreen`:
Add `final TtsService? ttsService;` parameter.
In `_playCardAudio`:
```dart
try {
  await _tts.speak(card.word, language: 'en-GB');
} catch (_) {
  final audioBytes = await widget.api.loadCardAudio(card.id);
  if (mounted) await _player.play(audioBytes);
}
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `cd mobile && flutter test test/features/learning_flow_test.dart`
Expected: PASS

- [ ] **Step 5: Commit Task 4**

```bash
git add mobile/
git commit -m "feat(mobile): integrate TtsService into flashcard deck, review, and speaking screens"
```

---

### Task 5: Full Regression, Docker Build, APK Build & Device Installation

**Files:**
- Modify: `docker-compose.yml` (if needed for speech dependencies)
- Artifact: `mobile/build/app/outputs/flutter-apk/app-debug.apk`

- [ ] **Step 1: Run full test suite and static analysis**

Run: `make test`
Expected: 100% pass (launcher, backend pytest, mobile flutter).
Run: `make analyze`
Expected: 0 issues found.

- [ ] **Step 2: Rebuild backend Docker containers**

Run: `docker compose -f docker-compose.yml -f compose.speech.yml up -d --build api speech-runtime`
Verify health via `docker compose ps` and `curl http://localhost:8000/api/v1/health` and `curl http://localhost:8010/health`.

- [ ] **Step 3: Build mobile debug APK**

Run: `cd mobile && flutter build apk --debug`
Expected: Successful build.

- [ ] **Step 4: Install APK to connected device**

Run: `$HOME/Android/Sdk/platform-tools/adb -s 324952517332 install -r mobile/build/app/outputs/flutter-apk/app-debug.apk`
Configure `reverse tcp:8000 tcp:8000` and relaunch app on device.

- [ ] **Step 5: Commit and push to origin/main**

```bash
git push origin main
```
