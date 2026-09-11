import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _image_bytes():
    image = Image.new("RGB", (2, 2), "white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_batch_extract_processes_files_concurrently_and_preserves_order():
    with patch("app.main.ocr_image", return_value={"text": "40% 750 ml", "boxes": []}) as ocr:
        response = TestClient(app).post(
            "/api/batch-extract",
            files=[
                ("files", ("first.png", _image_bytes(), "image/png")),
                ("files", ("second.png", _image_bytes(), "image/png")),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [item["filename"] for item in body["results"]] == ["first.png", "second.png"]
    assert ocr.call_count == 2


def test_batch_extract_uses_optional_application_brand():
    with patch("app.main.ocr_image", return_value={"text": "ACME BOURBON", "boxes": []}):
        response = TestClient(app).post(
            "/api/batch-extract",
            data={"application_brand": "ACME BOURBON"},
            files=[("files", ("label.png", _image_bytes(), "image/png"))],
        )

    assert response.status_code == 200
    assert response.json()["results"][0]["fields"]["brand_match"] is True


def test_batch_extract_returns_an_error_for_invalid_images():
    response = TestClient(app).post(
        "/api/batch-extract",
        files=[("files", ("not-an-image.txt", b"invalid", "text/plain"))],
    )

    assert response.status_code == 200
    assert response.json()["results"] == [
        {"filename": "not-an-image.txt", "error": "invalid image"}
    ]


def test_extract_rejects_files_over_10_mb():
    response = TestClient(app).post(
        "/api/extract",
        files=[("file", ("large.bin", b"x" * (10 * 1024 * 1024 + 1), "image/png"))],
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File too large"


def test_extract_rejects_invalid_images():
    response = TestClient(app).post(
        "/api/extract",
        files=[("file", ("invalid.txt", b"not an image", "text/plain"))],
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid image:")


def test_batch_extract_rejects_more_than_20_files():
    response = TestClient(app).post(
        "/api/batch-extract",
        files=[
            ("files", (f"file-{index}.png", _image_bytes(), "image/png"))
            for index in range(21)
        ],
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Max 20 files per request"
