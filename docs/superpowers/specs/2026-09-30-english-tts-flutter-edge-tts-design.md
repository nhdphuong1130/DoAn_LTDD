# Design Document: English Text-to-Speech Architecture (flutter_tts & edge-tts)

**Date**: 2026-09-30  
**Status**: Approved  
**Scope**: Mobile (`flutter_tts`), Backend Speech Runtime (`edge-tts`), Flashcard & Speaking Screens

---

## 1. Context & Motivation

In the previous implementation, the system used `VieNeu-TTS-v3-Turbo` inside `speech-runtime`. Because VieNeu is a dedicated Vietnamese Neural TTS model, pronouncing English vocabulary (e.g. *gardening*, *hobby*, *community*) resulted in unnatural, heavily accented, and phonetically incorrect speech (treating English letters as Vietnamese phonemes).

The learner needs authentic, clear, and standard English pronunciation aligned with the Vietnamese Grade 7 English curriculum (*Tiếng Anh 7 Global Success*, which teaches British English - `en-GB`, with American English - `en-US` familiarity).

To optimize responsiveness, offline capability, and server resources:
1. **Mobile Client**: Adopts `flutter_tts` to utilize native on-device TTS (Google TTS on Android, Apple AVSpeechSynthesizer on iOS). It provides zero latency, 100% offline functionality, and authentic native British (`en-GB`) / American (`en-US`) pronunciation.
2. **Backend Speech Runtime**: Replaces `VieNeu-TTS` with `edge-tts` (Microsoft Edge Neural TTS) providing human-quality British and American English voices. It acts as a robust server-side synthesis fallback and provides persistent cached `.wav` files via `GET /api/v1/flashcards/cards/{id}/audio`.

---

## 2. Architecture & Data Flow

```
                               Mobile Application
                    [Tap "Nghe phát âm tiếng Anh" / 🔊 Icon]
                                       │
                      ┌────────────────┴────────────────┐
                      ▼                                 ▼
           [Priority 1: Instant / Offline]     [Priority 2: Server Fallback]
           Native On-Device flutter_tts         GET /cards/{card_id}/audio
           - Language: en-GB (or en-US)         - Handled by FlashcardService
           - Engine: Google TTS / iOS TTS       - Cached via VocabAudioCache (.wav)
           - Latency: 0ms (no network)          - Backend synthesizes via edge-tts
```

---

## 3. Detailed Component Specifications

### 3.1. Mobile Client (`mobile/`)

1. **Dependency & Permissions**:
   - `flutter_tts: ^4.2.2` in `mobile/pubspec.yaml`.
   - Android query declaration in `mobile/android/app/src/main/AndroidManifest.xml`:
     ```xml
     <queries>
         <intent>
             <action android:name="android.intent.action.TTS_SERVICE" />
         </intent>
     </queries>
     ```
2. **TTS Abstraction (`mobile/lib/services/tts_service.dart`)**:
   - Interface:
     ```dart
     abstract interface class TtsService {
       Future<void> speak(String text, {String language = 'en-GB'});
       Future<void> stop();
       Future<void> dispose();
     }
     ```
   - Implementation:
     - `NativeTtsService`: Wraps `FlutterTts`, configures `en-GB`, speech rate (0.45 - 0.5 for learners), pitch (1.0).
     - `FakeTtsService`: In-memory recording of spoken texts for widget tests.
3. **Screen Integrations**:
   - **`DeckScreen` (`learning_screen.dart`)**:
     - Header icon `IconButton(Icons.volume_up)` and bottom action `FilledButton.tonalIcon` (`Nghe phát âm tiếng Anh`).
     - Tapping invokes `ttsService.speak(card.word, language: 'en-GB')`.
     - If `ttsService` fails (e.g. engine missing), gracefully falls back to `api.loadCardAudio(card.id)` played via `audioPlayer`.
   - **`ReviewScreen` (`review_screen.dart`)**:
     - Revealed card speaker icon `Icons.volume_up` calls `ttsService.speak(card.word)`.
   - **`SpeakingScreen` (`speaking_screen.dart`)**:
     - "Nghe mẫu tiếng Anh" button calls `ttsService.speak(card.word)`.

### 3.2. Backend Speech Runtime (`speech/`)

1. **Remove VieNeu & Add edge-tts**:
   - In `speech/requirements.txt`: Replace `vieneu` with `edge-tts`. Keep `faster-whisper` for speech recognition.
   - Update `speech/setup_speech.py` and `scripts/setup_speech.sh`.
2. **Engine Synthesis (`speech/engine.py`)**:
   - Supported English Voice Presets:
     - `en-GB-SoniaNeural` (Female - British, Default)
     - `en-GB-RyanNeural` (Male - British)
     - `en-US-JennyNeural` (Female - American)
     - `en-US-GuyNeural` (Male - American)
   - `voices()` returns the 4 standard English presets.
   - `synthesize(text, voice_id)` uses `edge_tts.Communicate(text, voice_id)` to produce high-fidelity audio, converted/streamed as WAV.
3. **Backend API (`backend/src/english7/modules/flashcards/`)**:
   - `VocabAudioCache.default_voice` defaults to `"en-GB-SoniaNeural"`.
   - `GET /api/v1/flashcards/cards/{id}/audio` returns cached/synthesized WAV file.

---

## 4. Error Handling & Edge Cases

| Scenario | Behavior |
| :--- | :--- |
| Mobile device has no Google TTS installed or disabled | Catches exception and falls back to backend `api.loadCardAudio(card.id)`. |
| Student leaves screen during TTS playback | `dispose()` immediately stops TTS playback (`tts.stop()`). |
| Backend edge-tts network glitch during synthesis | Retries or returns 503; if audio is already cached in `VocabAudioCache`, serves from disk cache instantly. |
| Non-Latin or blank word passed | Validation rejects blank strings; words are trimmed before synthesis. |

---

## 5. Testing & Verification Plan

1. **Unit & Widget Tests**:
   - Mobile: Widget tests with `FakeTtsService` verifying that `speak()` is called with `en-GB` on `DeckScreen`, `ReviewScreen`, and `SpeakingScreen`.
   - Backend: Unit tests in `backend/tests/modules/flashcards/test_audio.py` updated to verify `"en-GB-SoniaNeural"` voice ID.
   - Speech Runtime: Tests in `speech/test_app.py` verifying `/voices` returns English voices and `/synthesize` accepts `en-GB-SoniaNeural`.
2. **Full Regression**:
   - `make test`: All launcher, backend pytest, and mobile flutter tests pass.
   - `make analyze`: 0 issues found.
3. **Live Device Verification**:
   - Build APK (`flutter build apk --debug`).
   - Install to connected Android device (`adb install -r`).
   - Re-test voice playback to confirm authentic native English pronunciation.
