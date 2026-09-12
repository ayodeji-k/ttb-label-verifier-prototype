from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "TTB Label Verifier" in response.text


def test_invalid_batch_image_is_rejected():
    response = client.post(
        "/api/batch-extract",
        files={"files": ("invalid.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["results"] == [
        {"filename": "invalid.txt", "error": "invalid image"}
    ]
