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

# Ports & default command
EXPOSE 8000

# CRON
RUN apt-get update && apt-get install -y --no-install-recommends cron curl && rm -rf /var/lib/apt/lists/*
COPY ops/daily_train.sh /usr/local/bin/daily_train.sh
RUN chmod +x /usr/local/bin/daily_train.sh
RUN echo "0 2 * * * /usr/local/bin/daily_train.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/daily && \
    crontab /etc/cron.d/daily
CMD service cron start && python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 2
