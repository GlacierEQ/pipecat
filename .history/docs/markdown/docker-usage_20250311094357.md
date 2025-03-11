# Docker Deployment Guide

This document provides instructions for deploying Pipecat applications using Docker.

## Basic Usage

Build the Docker image:

```bash
docker build -f docker/Dockerfile -t pipecat .
```

Run the container:

```bash
docker run -p 8000:8000 pipecat
```

## Persisting Cache Data

For better performance across container restarts, you can persist cache data using volumes.

### Using Docker Run

```bash
docker run -p 8000:8000 -v pipecat_cache:/app/cache pipecat
```

### Using Docker Compose

We provide a `docker-compose.yml` file for convenience:

```bash
docker-compose up
```

This automatically sets up a named volume for cache persistence.

## Environment Variables

The following environment variables can be used to configure the container:

- `PIPECAT_CACHE_DIR`: Directory for persistent cache (default: `/app/cache`)
- `PIPECAT_LOG_LEVEL`: Set logging level (default: `INFO`)
- `PIPECAT_DEBUG`: Enable debug mode (`true` or `false`, default: `false`)

## Custom Configuration

You can bind-mount a custom `.env` file:

```bash
docker run -p 8000:8000 -v ./my-env-file:/app/.env -v pipecat_cache:/app/cache pipecat
```

## Container Structure

- `/app`: Application code
- `/app/cache`: Persistent cache directory
