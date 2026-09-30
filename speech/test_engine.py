import io
import wave

import pytest

from speech.engine import decode_audio


def wav(seconds, sample=b"\x00\x20"):
    output = io.BytesIO()
    with wave.open(output, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(16000)
        file.writeframes(sample * int(seconds * 16000))
    return output.getvalue()


def test_decoded_duration_limit():
    assert len(decode_audio(wav(15.5))) == 248000
    with pytest.raises(ValueError, match="exceeds"):
        decode_audio(wav(16.1))


@pytest.mark.parametrize("data", [wav(1, b"\0\0"), wav(0.05), b"not audio"])
def test_silence_short_and_invalid_audio(data):
    with pytest.raises(ValueError):
        decode_audio(data)
