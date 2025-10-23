#!/usr/bin/env bash
set -euo pipefail

#Basic Auth
USER="${API_USER:-admin}"
PASS="${API_PASS:-changeme}"

# -fS：if HTTP not 2xx then print error, but keep the container || true
curl -fS -u "${USER}:${PASS}" \
  -H "Content-Type: application/json" \
  -X POST "http://localhost:8000/training" || true
