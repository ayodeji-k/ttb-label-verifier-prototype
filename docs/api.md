# API reference

The service exposes a single-image endpoint and a batch endpoint. Neither
endpoint stores uploaded images.

## `POST /api/extract`

Accepts a multipart form with:

- `file`: one PNG, JPEG, or other Pillow-supported image.
- `application_brand`: optional expected brand name used for fuzzy matching.

The response contains `fields`, the extracted `ocr_text`, and `latency_ms`.

## `POST /api/batch-extract`

Accepts one or more multipart fields named `files`:

```sh
curl \
  -F "files=@path/to/label1.png" \
  -F "files=@path/to/label2.png" \
  http://localhost:8000/api/batch-extract
```

The endpoint processes images concurrently and returns results in upload order.
Each item contains its filename, parsed fields, OCR text, and latency. An
unreadable image produces an item with `error: "invalid image"` without
discarding the other results.

The checked-in files in `sample_data/` are OCR text fixtures used to document
the expected label content. Convert them to images before sending them to the
image endpoints.
