FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV and Torch
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# We use 1 worker for ML stability, but with A1 Flex (4-8 OCPU), 
# we could potentially use more if we want to increase throughput later.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4141", "--workers", "1"]
