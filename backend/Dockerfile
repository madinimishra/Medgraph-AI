# syntax=docker/dockerfile:1
FROM python:3.10-slim

WORKDIR /app

# System dependencies:
# - libpq-dev + gcc: build psycopg2 / other native extensions if needed
# - poppler-utils: pdf2image (scanned-PDF OCR fallback)
# - libmagic1: python-magic file-type sniffing
# - libgl1, libglib2.0-0: required by opencv-python-headless at import time
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    poppler-utils \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# torch's default Linux wheel pulls in the full nvidia-*-cuXX dependency
# chain (cudnn/cublas/cufft/... - several hundred MB each) even though
# this app only ever runs torch on CPU (sentence-transformers embeddings).
# Installing the CPU-only build first means torch's own metadata never
# declares those CUDA dependencies, so the requirements.txt pass below
# just finds torch already satisfied instead of pulling gigabytes of
# unused CUDA libraries - this was also the actual cause of repeated
# "hash mismatch" build failures: those were always a huge nvidia-cu*
# wheel getting corrupted mid-download on a large transfer, not a real
# package integrity problem.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.13.0 torchvision==0.28.0 --extra-index-url https://download.pytorch.org/whl/cpu

# A pip cache mount means anything already downloaded and verified isn't
# re-fetched on retry, and the retry loop covers any remaining transient
# network failures on the rest of the dependency list.
RUN --mount=type=cache,target=/root/.cache/pip \
    sh -c ' \
    for i in 1 2 3 4 5; do \
        pip install -r requirements.txt && exit 0; \
        echo "pip install attempt $i failed, retrying..."; \
        sleep 5; \
    done; \
    exit 1'

COPY . .

RUN mkdir -p app/uploads app/logs chroma_db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
