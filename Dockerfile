# Stage-1: one-shot runner for Signal.ai
FROM python:3.11-slim

# Minimal system deps
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# App dir
WORKDIR /app

# Install Python deps first (cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY signalai.py ./signalai.py

# Default command expects mounted volumes for config, store, and outputs
ENTRYPOINT ["python", "signalai.py"]
