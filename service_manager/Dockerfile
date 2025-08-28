# ---- Base Image ----
FROM python:3.11-slim-bullseye AS base

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

# ---- System Dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
 && rm -rf /var/lib/apt/lists/*

# ---- Python Dependencies (cache-friendly) ----
COPY requirements.txt /app/

# Upgrade pip tooling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Cache pip downloads between builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ---- Application Source ----
COPY . /app

# ---- Create Non-Root User ----
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# ---- Runtime Entrypoint ----
EXPOSE 8100

# Healthcheck (optional, for prod orchestrators)
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#   CMD curl -f http://localhost:8100/health || exit 1

# Start FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]

