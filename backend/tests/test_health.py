from fastapi.testclient import TestClient

from english7.main import app


def test_health_returns_service_status() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "english7-api"}

