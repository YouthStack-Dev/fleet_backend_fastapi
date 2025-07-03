FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose correct port (should match uvicorn --port)
EXPOSE 8100

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
