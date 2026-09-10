# Architecture

The prototype is split into a small FastAPI backend and a static browser
frontend.

## Request flow

1. The frontend sends an image as multipart form data to `/api/extract` or
   `/api/batch-extract`.
2. FastAPI reads the upload and Pillow decodes it into an RGB image.
3. `backend/app/ocr.py` preprocesses the image and invokes Tesseract.
4. `backend/app/parsers.py` applies regex and fuzzy matching rules to the OCR
   text.
5. The API returns parsed fields, OCR text, and processing latency. Uploaded
   images are not persisted.

Batch requests use `asyncio` for request coordination and a bounded
`ThreadPoolExecutor` for blocking OCR calls. `asyncio.gather` preserves the
order of the uploaded files in the response while allowing independent OCR
jobs to run concurrently.

## Deployment

The Docker image runs Uvicorn on port 8000 and serves the backend and static
frontend from the repository. `docker-compose.yml` provides the same service
for local development.
