FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for building & git-based installs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential gcc libpq-dev libssl-dev git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (should match uvicorn port)
EXPOSE 8100

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
