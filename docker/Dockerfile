# Use a specific Python version for better reproducibility
FROM python:3.13.2-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -e ".[all]"

# Default command
CMD ["python", "-m", "pipecat.cli"]
