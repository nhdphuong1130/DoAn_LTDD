from unittest.mock import MagicMock, patch
from io import BytesIO

from english7.main import app


def test_get_audio_by_track_returns_audio_stream(client):
    mock_response = MagicMock()
    mock_response.read.return_value = b"fake-mp3-audio-bytes"

    mock_client = MagicMock()
    mock_client.get_object.return_value = mock_response

    with patch("english7.modules.media.router._get_minio_client", return_value=mock_client):
        response = client.get("/api/v1/media/audio/2")
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert response.content == b"fake-mp3-audio-bytes"


def test_get_audio_by_track_not_found(client):
    with patch("english7.modules.media.router._get_minio_client", return_value=None):
        with patch("os.path.exists", return_value=False):
            response = client.get("/api/v1/media/audio/999")
            assert response.status_code == 404


def test_get_image_by_filename_success(client):
    mock_response = MagicMock()
    mock_response.read.return_value = b"\x89PNG\r\n\x1a\nfake-png-bytes"

    mock_client = MagicMock()
    mock_client.get_object.return_value = mock_response

    with patch("english7.modules.media.router._get_minio_client", return_value=mock_client):
        response = client.get("/api/v1/media/image/unit-1-act3-pic1.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"\x89PNG\r\n\x1a\nfake-png-bytes"


def test_get_image_by_filename_not_found(client):
    with patch("english7.modules.media.router._get_minio_client", return_value=None):
        with patch("os.path.exists", return_value=False):
            response = client.get("/api/v1/media/image/nonexistent.png")
            assert response.status_code == 404


def test_get_image_by_filename_invalid_filename(client):
    response = client.get("/api/v1/media/image/..%2F..%2Fsecret.png")
    assert response.status_code in (400, 404)

