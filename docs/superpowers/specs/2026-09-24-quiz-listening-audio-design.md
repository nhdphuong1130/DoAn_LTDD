<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Quiz Listening Audio Integration Design

## 1. Problem Statement
In the current Mobile Quiz flow, an audio player widget (`LimitedAudioPlayer`) is displayed statically on every quiz session, displaying "Lượt nghe còn lại: 0" after clicks, but it neither plays audio nor connects to any textbook audio track. Furthermore, the quiz generator creates purely reading-based True/False/Not given questions from random textbook fragments.

Students need the ability to select the exam mode:
- **Listening (`listening`)**: Quizzes derived from authentic textbook listening activities (e.g. *Skills 2 - Listening* or *A Closer Look 1 - Pronunciation*) with their corresponding audio stream (`/api/v1/media/audio/{track_number}`).
- **Reading & Language (`reading`)**: Reading comprehension, grammar, and vocabulary without audio distraction (audio player hidden).
- **Mixed (`mixed`)**: Comprehensive test featuring both listening questions with authentic audio playback and reading questions.

## 2. Architecture & Data Contracts

### 2.1 Backend Contract Changes
- **`GenerateQuizRequest`** (`english7/modules/quizzes/router.py`):
  - Add `mode: str = "mixed"` with allowed values: `["listening", "reading", "mixed"]`.
- **`QuizOptionsResponse`**:
  - Add `modes: list[str] = ["listening", "reading", "mixed"]`.
- **`QuizResponse`**:
  - Add `audio_url: str | None = None` (resolved relative media path, e.g. `/api/v1/media/audio/37`).
  - Add `audio_title: str | None = None` (e.g., `Unit 5 - Skills 2 (Track 37)`).
- **`QuizDraft`** domain model:
  - Add `audio_url: str | None = None`.
  - Add `audio_title: str | None = None`.

### 2.2 Question Generation Strategy (`GroundedQuestionGenerator`)
1. **Listening Mode (`listening`)**:
   - Query textbook activities with associated `audio_tracks` (where activity belongs to *Skills 2* or instruction mentions *listen*).
   - Randomly or adaptively select a listening activity and its `AudioTrack`.
   - Extract activity items/statements or generate questions grounded in this listening activity's text/transcript.
   - Set `audio_url = f"/api/v1/media/audio/{track.track_number}"`.
2. **Reading Mode (`reading`)**:
   - Query verified textbook reading fragments (`SourceFragment`).
   - Generate reading comprehension questions.
   - `audio_url = None`.
3. **Mixed Mode (`mixed`)**:
   - Split question count: first half or designated block from a listening activity (with `audio_url`), remaining from reading fragments.
   - Set `audio_url = f"/api/v1/media/audio/{track.track_number}"`.

### 2.3 Mobile App Contract & UI
- **`QuizSetup`** model (`mobile/lib/app/student_api.dart`):
  - Add `final String mode;` (defaults to `'mixed'`).
- **`QuizOptions`** model:
  - Add `final List<String> modes;`.
- **`QuizSession`** model:
  - Add `final String? audioUrl;`.
  - Add `final String? audioTitle;`.
- **`QuizScreen`** (`mobile/lib/features/quizzes/quiz_screen.dart`):
  - Add mode selector chips in creation form:
    - 🎧 Kỹ năng Nghe (Listening)
    - 📖 Đọc hiểu & Ngôn ngữ (Reading)
    - 📝 Đề thi Tổng hợp (Mixed)
  - During test:
    - If `session.audioUrl != null`: Show `LimitedAudioPlayer`, wire `onPlay` to `NativeAudioPlayer.play(resolvedUrl)`.
    - If `session.audioUrl == null`: Omit `LimitedAudioPlayer` completely.
- **Audio Playback Constraints**:
  - Max 2 plays per session.
  - Disable seeking.
  - Decrement play count atomically and stop playback on quiz submission.

## 3. Testing & Verification
1. **Backend Tests**:
   - Unit tests for `GroundedQuestionGenerator` generating listening questions with `audio_url`.
   - Endpoint test for `POST /api/v1/quizzes` with `mode="listening"`, `mode="reading"`, `mode="mixed"`.
2. **Mobile Tests**:
   - Widget tests for `QuizScreen`:
     - Select mode -> creates quiz with chosen mode.
     - With `audioUrl != null` -> displays `LimitedAudioPlayer` and triggers audio play.
     - With `audioUrl == null` -> `LimitedAudioPlayer` is absent.
