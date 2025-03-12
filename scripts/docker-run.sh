#!/bin/bash
# Automated script to build and run pipecat in Docker

set -e  # Exit on error

# Default configuration
DEFAULT_MODE="prod"
DEFAULT_COMMAND="dashboard"
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8080"
IMAGE_NAME="pipecat"
CONTAINER_NAME="pipecat-server"

# Parse command line arguments
MODE="${1:-$DEFAULT_MODE}"  # prod or dev
COMMAND="${2:-$DEFAULT_COMMAND}"  # dashboard, api, etc.
HOST="${3:-$DEFAULT_HOST}"
PORT="${4:-$DEFAULT_PORT}"

echo "🚀 Starting Pipecat Docker automation..."

# Detect Docker or Podman
if command -v docker &> /dev/null; then
    DOCKER_CMD=docker
elif command -v podman &> /dev/null; then
    DOCKER_CMD=podman
    echo "Using Podman instead of Docker"
else
    echo "❌ Error: Neither Docker nor Podman is installed"
    exit 1
fi

# Ensure Docker daemon is running
if ! $DOCKER_CMD info > /dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not running"
    exit 1
fi

# Determine which Dockerfile to use based on mode
if [[ "$MODE" == "dev" ]]; then
    DOCKERFILE="docker/Dockerfile.dev"
    IMAGE_TAG="dev"
    CONTAINER_NAME="pipecat-dev"
    ADDITIONAL_ARGS="--volume $(pwd):/workspaces/pipecat"
else
    DOCKERFILE="docker/Dockerfile"
    IMAGE_TAG="latest" 
    CONTAINER_NAME="pipecat-server"
    ADDITIONAL_ARGS=""
fi

# Build the Docker image
echo "🔧 Building Docker image..."
$DOCKER_CMD build -t "$IMAGE_NAME:$IMAGE_TAG" -f "$DOCKERFILE" .

# Check if we already have a container with this name
if $DOCKER_CMD ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo "🧹 Removing existing container..."
    $DOCKER_CMD rm -f "$CONTAINER_NAME"
fi

# Create and run the container
echo "🚀 Starting container with command: $COMMAND --host $HOST --port $PORT"
$DOCKER_CMD run --name "$CONTAINER_NAME" \
    -p "$PORT:$PORT" \
    -e "PIPECAT_CACHE_DIR=/app/cache" \
    -v "pipecat_cache:/app/cache" \
    $ADDITIONAL_ARGS \
    -d "$IMAGE_NAME:$IMAGE_TAG" "$COMMAND" "--host" "$HOST" "--port" "$PORT"

echo "✅ Container started! Access the service at http://localhost:$PORT"
echo "📖 View logs with: $DOCKER_CMD logs -f $CONTAINER_NAME"
echo "🛑 Stop with: $DOCKER_CMD stop $CONTAINER_NAME"
