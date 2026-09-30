import hashlib
import re
import unicodedata
from typing import Protocol
from english7.api.errors import ApplicationError

MAX_AUDIO_BYTES = 2 * 1024 * 1024

CONTRACTION_MAP = {
    "i'm": ['i', 'am'],
    "you're": ['you', 'are'],
    "we're": ['we', 'are'],
    "they're": ['they', 'are'],
    "he's": ['he', 'is'],
    "she's": ['she', 'is'],
    "it's": ['it', 'is'],
    "don't": ['do', 'not'],
    "doesn't": ['does', 'not'],
    "didn't": ['did', 'not'],
    "can't": ['can', 'not'],
    "cannot": ['can', 'not'],
    "won't": ['will', 'not'],
    "isn't": ['is', 'not'],
    "aren't": ['are', 'not'],
    "wasn't": ['was', 'not'],
    "weren't": ['were', 'not'],
}


def words(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?|[0-9]+", unicodedata.normalize('NFKC', text).replace('’', "'").casefold())


def char_similarity(w1: str, w2: str) -> float:
    if w1 == w2:
        return 1.0
    if not w1 or not w2:
        return 0.0
    len1, len2 = len(w1), len(w2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if w1[i - 1] == w2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    dist = dp[len1][len2]
    return max(0.0, 1.0 - dist / max(len1, len2))


def compare_words(prompt, transcript):
    """Duolingo-style word alignment and evaluation.

    Evaluates each expected word against the recognized speech transcript,
    accommodating contractions, minor phonetic/inflection variations, and filler words.
    """
    expected, actual = words(prompt), words(transcript)
    if not expected or len(expected) > 80 or len(actual) > 200:
        raise ApplicationError('invalid_speech_text', 'Please practise a short English phrase', 422)

    n, m = len(expected), len(actual)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sim = char_similarity(expected[i - 1], actual[j - 1])
            # Contraction equality check
            if expected[i - 1] in CONTRACTION_MAP and actual[j - 1] in CONTRACTION_MAP[expected[i - 1]]:
                sim = max(sim, 0.9)
            elif actual[j - 1] in CONTRACTION_MAP and expected[i - 1] in CONTRACTION_MAP[actual[j - 1]]:
                sim = max(sim, 0.9)
            dp[i][j] = max(
                dp[i - 1][j],
                dp[i][j - 1],
                dp[i - 1][j - 1] + (sim if sim >= 0.72 else 0.0),
            )

    # Backtrack alignment
    i, j = n, m
    matched_actual = {}
    while i > 0 and j > 0:
        sim = char_similarity(expected[i - 1], actual[j - 1])
        if expected[i - 1] in CONTRACTION_MAP and actual[j - 1] in CONTRACTION_MAP[expected[i - 1]]:
            sim = max(sim, 0.9)
        elif actual[j - 1] in CONTRACTION_MAP and expected[i - 1] in CONTRACTION_MAP[actual[j - 1]]:
            sim = max(sim, 0.9)

        if sim >= 0.72 and abs(dp[i][j] - (dp[i - 1][j - 1] + sim)) < 1e-6:
            matched_actual[i - 1] = (j - 1, sim)
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j]:
            i -= 1
        else:
            j -= 1

    evaluations = []
    missing = []
    for idx, exp in enumerate(expected):
        if idx in matched_actual:
            act_idx, sim = matched_actual[idx]
            status = 'correct' if sim >= 0.90 else 'near'
            score = 100 if sim >= 0.90 else 85
            heard = actual[act_idx]
        else:
            status = 'missing'
            score = 0
            heard = None
            missing.append(exp)
        evaluations.append({'word': exp, 'status': status, 'score': score, 'heard': heard})

    matched_act_indices = {v[0] for v in matched_actual.values()}
    extra = [act for idx, act in enumerate(actual) if idx not in matched_act_indices]

    base_score = sum(e['score'] for e in evaluations) / len(evaluations)
    excess = max(0, len(actual) - len(expected))
    penalty = min(10.0, excess * 2.5)
    match_percent = max(0, min(100, round(base_score - penalty)))

    return {
        'match_percent': match_percent,
        'missing_words': missing,
        'extra_words': extra,
        'word_evaluations': evaluations,
    }


class SpeechRuntime(Protocol):
    def voices(self) -> list[dict]: ...
    def transcribe(self, audio: bytes) -> dict: ...
    def synthesize(self, text: str, voice_id: str) -> bytes: ...


class SpeakingService:
    def __init__(self, repository, cards, runtime: SpeechRuntime):
        self.repository, self.cards, self.runtime = repository, cards, runtime

    def voices(self, user_id):
        selected = self.repository.voice(user_id)
        try:
            voices = self.runtime.voices()
        except ApplicationError:
            return {'items': [], 'selected_voice': selected, 'available': False}
        return {'items': voices, 'selected_voice': selected, 'available': bool(voices)}

    def _require_voice(self, voice):
        if voice not in {v['id'] for v in self.runtime.voices()}:
            raise ApplicationError('invalid_voice', 'Please choose an available tutor voice', 422)

    def set_voice(self, user, voice):
        self._require_voice(voice)
        self.repository.set_voice(user, voice)
        return {'voice_id': voice}

    def preview(self, voice):
        self._require_voice(voice)
        return self.runtime.synthesize('Chào em! Mình cùng học từ vựng và luyện nói tiếng Anh nhé.', voice)

    def submit(self, user, request, card_id, voice, audio, *, prompt: str | None = None):
        if not audio or len(audio) > MAX_AUDIO_BYTES:
            raise ApplicationError('invalid_recording', 'Recording is empty or too large', 422)
        digest = hashlib.sha256(str(card_id).encode() + b'\0' + voice.encode() + b'\0' + (prompt or '').encode() + b'\0' + audio).hexdigest()
        previous = self.repository.existing(user, request, digest)
        if previous:
            return previous
        card = self.cards.get_card(user, card_id)
        if prompt is None or not prompt.strip():
            # Default to full example sentence if present, otherwise vocabulary word
            prompt = card.example if hasattr(card, 'example') and card.example and card.example.strip() else card.word
        if not words(prompt) or len(words(prompt)) > 80:
            raise ApplicationError('invalid_prompt', 'Please choose a short English word or phrase', 422)
        self._require_voice(voice)
        recognized = self.runtime.transcribe(audio)
        transcript = recognized['transcript'].strip()
        if not words(transcript):
            raise ApplicationError('no_speech', 'Chưa nghe rõ lời nói. Em hãy thu lại nhé.', 422)
        result = compare_words(prompt, transcript)
        score = result['match_percent']
        if score >= 85:
            feedback = 'Tuyệt vời! Em phát âm rất chuẩn và rõ ràng.'
        elif score >= 70:
            feedback = 'Rất tốt! Bản thu đã khớp phần lớn câu mẫu. Em nghe lại câu mẫu để hoàn thiện nhé.'
        elif score >= 50:
            feedback = 'Khá tốt! Em hãy bấm nghe chậm để luyện lại các từ chưa chuẩn và thử lại nhé.'
        else:
            feedback = 'Chưa nhận rõ câu nói. Em hãy bấm nút 🐢 nghe chậm từng từ rồi phát âm lại nhé.'
        result['feedback'] = feedback
        result['comparison_version'] = 'duolingo-word-align-v2'
        return self.repository.save(user, request, card_id, digest, voice, recognized.get('model', 'unknown'),
                                    prompt, transcript, card.source_label, result)

    def history(self, user):
        return self.repository.history(user)

    def feedback_audio(self, user, attempt):
        result, voice = self.repository.get(user, attempt)
        return self.runtime.synthesize(result['feedback'], voice)

    def progress(self, user):
        return {**self.cards.progress(user), 'speaking_count': self.repository.count(user),
                'recent_speaking': self.history(user)[:5]}
