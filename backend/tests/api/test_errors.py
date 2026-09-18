def test_unknown_route_uses_standard_error(client) -> None:
    response = client.get("/api/v1/unknown")

    body = response.json()
    assert response.status_code == 404
    assert set(body) == {"code", "message", "details", "trace_id"}
    assert body["code"] == "not_found"


def test_trace_id_is_returned_as_header(client) -> None:
    response = client.get("/api/v1/unknown")

    assert response.headers["x-trace-id"] == response.json()["trace_id"]


def test_client_trace_id_is_preserved(client) -> None:
    response = client.get(
        "/api/v1/unknown",
        headers={"X-Trace-ID": "student-request-42"},
    )

    assert response.headers["x-trace-id"] == "student-request-42"
    assert response.json()["trace_id"] == "student-request-42"

