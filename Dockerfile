# Dockerfile
FROM python:3.12-slim

# System deps (optional but useful for MLflow local file store)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy dependency spec first (better cache)
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /workspace

# Ports & default command (overridden by docker-compose)
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
