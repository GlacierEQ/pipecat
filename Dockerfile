FROM python:3.14.2-slim

WORKDIR /app

# Install build dependencies and tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements*.txt pyproject.toml ./
COPY pipecat/ ./pipecat/
COPY README.md ./
COPY setup.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Build and install the project
RUN pip install -e .

# Expose the port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "pipecat.wsgi:app"]
