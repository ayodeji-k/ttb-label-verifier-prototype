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


def test_batch_extract_supports_one_brand_per_file():
    with patch("app.main.ocr_image", return_value={"text": "label", "boxes": []}), patch(
        "app.main.parse_fields", return_value={}
    ) as parse:
        response = TestClient(app).post(
            "/api/batch-extract",
            data={"application_brand": ["ACME BOURBON", "EXAMPLE VODKA"]},
            files=[
                ("files", ("first.png", _image_bytes(), "image/png")),
                ("files", ("second.png", _image_bytes(), "image/png")),
            ],
        )

    assert response.status_code == 200
    assert {args for args, _ in parse.call_args_list} == {
        ("label", "ACME BOURBON"),
        ("label", "EXAMPLE VODKA"),
    }


def test_batch_extract_rejects_mismatched_brand_count():
    response = TestClient(app).post(
        "/api/batch-extract",
        data={"application_brand": ["ACME BOURBON", "EXAMPLE VODKA"]},
        files=[("files", ("only.png", _image_bytes(), "image/png"))],
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Provide one application_brand or one brand per file"


def test_batch_extract_returns_an_error_for_invalid_images():
    response = TestClient(app).post(
        "/api/batch-extract",
        files=[("files", ("not-an-image.png", b"invalid", "image/png"))],
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["filename"] == "not-an-image.png"
    assert response.json()["results"][0]["error"].startswith("invalid image:")


def test_extract_rejects_files_over_10_mb():
    response = TestClient(app).post(
        "/api/extract",
        files=[("file", ("large.png", b"x" * (10 * 1024 * 1024 + 1), "image/png"))],
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File too large"


def test_extract_rejects_invalid_images():
    response = TestClient(app).post(
        "/api/extract",
        files=[("file", ("invalid.png", b"not an image", "image/png"))],
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid image:")


def test_health_check():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "TTB Label Verifier"}


def test_extract_rejects_unsupported_file_type():
    response = TestClient(app).post(
        "/api/extract",
        files=[("file", ("label.txt", b"not an image", "text/plain"))],
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid file type.")


def test_extract_rejects_empty_files():
    response = TestClient(app).post(
        "/api/extract",
        files=[("file", ("empty.png", b"", "image/png"))],
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


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
