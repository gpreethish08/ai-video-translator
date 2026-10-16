# Base image with Python 3.10 and FFmpeg
FROM python:3.10-slim

# Install system dependencies (FFmpeg, git, build essentials)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application source code
COPY . /app

# Create necessary folders
RUN mkdir -p /app/backend/uploads /app/backend/outputs /app/backend/temp /app/database

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
