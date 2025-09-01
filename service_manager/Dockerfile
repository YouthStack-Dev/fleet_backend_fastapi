# ---- Base Image ----
FROM python:3.11-slim-bookworm AS base
# ^ Use bookworm (newer Debian release) instead of bullseye to avoid stale apt mirrors

# ---- Environment Variables ----
# DEBIAN_FRONTEND=noninteractive → avoids interactive prompts during apt install
# PYTHONUNBUFFERED=1 → log output appears immediately (no buffering)
# PYTHONDONTWRITEBYTECODE=1 → avoids writing .pyc files
# PATH → ensure user-local bin is in PATH
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"


WORKDIR /app

# ---- System Dependencies ----
# Everything needed to build Python deps like psycopg2 / numpy
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
# ^ keep update + install + clean in ONE layer to avoid cache issues & shrink image

# ---- Python Dependencies ----
COPY requirements.txt /app/

# Upgrade pip tooling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install project dependencies (cache pip downloads between builds)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ---- Application Source ----
COPY . /app

# ---- Non-Root User ----
RUN useradd -m appuser && chown -R appuser /app
USER appuser
# ^ running as non-root is a best practice for security

# ---- Runtime ----
EXPOSE 8100
# ^ container metadata (for docs/orchestrators, doesn’t actually open the port)

# Optional healthcheck (useful in Docker Swarm / Kubernetes)
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#   CMD curl -f http://localhost:8100/health || exit 1

# ---- Entrypoint ----
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
