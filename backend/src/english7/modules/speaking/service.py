import hashlib
import re
import unicodedata
from typing import Protocol
from english7.api.errors import ApplicationError

MAX_AUDIO_BYTES = 2 * 1024 * 1024


def words(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?|[0-9]+", unicodedata.normalize('NFKC', text).replace('’', "'").casefold())


def compare_words(prompt, transcript):
    """Levenshtein word alignment. This is NOT an acoustic pronunciation score."""
    expected, actual = words(prompt), words(transcript)
    if not expected or len(expected) > 80 or len(actual) > 200:
        raise ApplicationError('invalid_speech_text', 'Please practise a short English phrase', 422)
    costs = [[0] * (len(actual) + 1) for _ in range(len(expected) + 1)]
    for i in range(len(expected) + 1):
        costs[i][0] = i
    for j in range(len(actual) + 1):
        costs[0][j] = j
    for i in range(1, len(expected) + 1):
        for j in range(1, len(actual) + 1):
            costs[i][j] = min(costs[i - 1][j] + 1, costs[i][j - 1] + 1,
                              costs[i - 1][j - 1] + (expected[i - 1] != actual[j - 1]))
    i, j = len(expected), len(actual)
    missing, extra = [], []
    while i or j:
        if i and j and costs[i][j] == costs[i - 1][j - 1] + (expected[i - 1] != actual[j - 1]):
            if expected[i - 1] != actual[j - 1]:
                missing.append(expected[i - 1]); extra.append(actual[j - 1])
            i -= 1; j -= 1
        elif i and costs[i][j] == costs[i - 1][j] + 1:
            missing.append(expected[i - 1]); i -= 1
        else:
            extra.append(actual[j - 1]); j -= 1
    return {'match_percent': round(100 * max(0, 1 - costs[-1][-1] / len(expected))),
            'missing_words': list(reversed(missing)), 'extra_words': list(reversed(extra))}


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

    def submit(self, user, request, card_id, voice, audio):
        if not audio or len(audio) > MAX_AUDIO_BYTES:
            raise ApplicationError('invalid_recording', 'Recording is empty or too large', 422)
        digest = hashlib.sha256(str(card_id).encode() + b'\0' + voice.encode() + b'\0' + audio).hexdigest()
        previous = self.repository.existing(user, request, digest)
        if previous:
            return previous
        card = self.cards.get_card(user, card_id)
        prompt = card.word
        if not words(prompt) or len(words(prompt)) > 80:
            raise ApplicationError('invalid_prompt', 'Please choose a short English word or phrase', 422)
        self._require_voice(voice)
        recognized = self.runtime.transcribe(audio)
        transcript = recognized['transcript'].strip()
        if not words(transcript):
            raise ApplicationError('no_speech', 'Chưa nghe rõ lời nói. Em hãy thu lại nhé.', 422)
        result = compare_words(prompt, transcript)
        if result['match_percent'] == 100:
            feedback = 'Máy nhận ra đầy đủ từ trong mẫu. Em hãy nghe lại bản thu để tiếp tục luyện nhé.'
        else:
            feedback = 'Máy chưa nhận ra đúng toàn bộ câu mẫu. Em xem các từ được đánh dấu, đọc chậm và thử lại nhé.'
        result['feedback'] = feedback + ' Đây là mức độ khớp lời nhận dạng, không phải điểm phát âm.'
        result['comparison_version'] = 'word-edit-v1'
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
