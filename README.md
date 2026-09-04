# TTB Label Verifier Prototype

This repository contains a scaffolded prototype for an AI-powered alcohol label verification app.

Quickstart (Docker):

1. Build the image:

   docker build -t ttb-label-proto .

2. Run the container:

   docker run --rm -p 8000:8000 ttb-label-proto

3. Open the frontend in your browser:

   http://localhost:8000/frontend/index.html

Quickstart (local):

1. Create a Python venv and install requirements:

   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt

2. Run the app:

   uvicorn backend.app.main:app --reload --port 8000

3. Open the frontend at:

   http://localhost:8000/frontend/index.html

API examples:

- Single image:
  curl -F "file=@sample_data/label1.jpg" http://localhost:8000/api/extract

- Batch images:
  curl -F "files=@sample_data/label1.jpg" -F "files=@sample_data/label2.jpg" http://localhost:8000/api/batch-extract

Notes:
- This is a lightweight prototype using pytesseract for OCR and regex/fuzzy rules for parsing.
- No images are stored by default.
