# ──────────────────────────────────────────────────────────
# Student Data Engineering Pipeline — Production Image
# ──────────────────────────────────────────────────────────
FROM python:3.11-slim

# Metadata
LABEL maintainer="Student"
LABEL description="Student Data Engineering Pipeline"

# Prevent Python from writing .pyc + enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies first (leverage Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY pytest.ini .

# Create data/logs directories
RUN mkdir -p data/raw data/processed logs

# Default command
CMD ["python", "main.py"]
