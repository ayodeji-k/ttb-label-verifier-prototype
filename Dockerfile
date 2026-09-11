# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install tesseract for OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    pkg-config \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app
ENV PYTHONPATH=/app/backend

# Copy backend
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
