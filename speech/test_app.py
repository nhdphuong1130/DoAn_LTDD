from fastapi.testclient import TestClient


class Engine:
    def voices(self):
        return [{"id": "mai", "name": "Mai Anh"}]

    def transcribe(self, data):
        if data == b"silence":
            raise ValueError("No speech detected; please record again")
        return {"transcript": "my hobby", "model": "stub"}

    def synthesize(self, text, voice_id):
        return b"RIFFtestWAVE"


def client():
    from speech.app import create_app
    return TestClient(create_app(Engine()))


def test_health_and_voices():
    assert client().get("/health").json()["available"] is True
    assert client().get("/voices").json() == {
        "items": [{"id": "mai", "name": "Mai Anh"}], "available": True
    }


def test_transcript_and_silence():
    response = client().post("/transcribe", files={"audio": ("clip.wav", b"audio")})
    assert response.json() == {"transcript": "my hobby", "model": "stub"}
    assert client().post("/transcribe", files={"audio": ("clip.wav", b"silence")}).status_code == 422


def test_upload_limit():
    response = client().post("/transcribe", files={"audio": ("clip.wav", b"a" * (2 * 1024 * 1024 + 1))})
    assert response.status_code == 413


def test_tts_validation_and_wav():
    assert client().post("/synthesize", json={"text": "Xin chào", "voice_id": "mai"}).headers["content-type"] == "audio/wav"
    assert client().post("/synthesize", json={"text": "Xin chào", "voice_id": "unknown"}).status_code == 422
    for text in ("", "   ", "x" * 401):
        assert client().post("/synthesize", json={"text": text, "voice_id": "mai"}).status_code == 422


def test_unavailable_and_empty_upload():
    from speech.app import create_app
    unavailable = TestClient(create_app())
    assert unavailable.get("/voices").json() == {"items": [], "available": False}
    assert unavailable.post("/synthesize", json={"text": "Xin chào", "voice_id": "mai"}).status_code == 503
    assert client().post("/transcribe", files={"audio": ("empty.wav", b"")}).status_code == 422


def test_model_error_is_sanitized():
    from speech.app import create_app

    class Broken(Engine):
        def transcribe(self, data):
            raise RuntimeError("private model file path")

    response = TestClient(create_app(Broken())).post("/transcribe", files={"audio": ("clip.wav", b"audio")})
    assert response.status_code == 503
    assert "private" not in response.text
