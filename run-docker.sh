#!/bin/bash
# Quick script to build and run Pipecat in Docker

# Default configuration
MODE=${1:-"prod"}  # "prod" or "dev"
COMMAND=${2:-"dashboard"}  # "dashboard", "api", etc.
HOST=${3:-"0.0.0.0"}
PORT=${4:-"8080"}

# Run the deployment script
python scripts/docker-deploy.py docker \
    --tag latest \
    --build-type Release \
    --port "$PORT" \
    --command "$COMMAND" \
    --apply

echo "✨ Pipecat is now running in Docker!"
echo "📊 Access the application at: http://localhost:$PORT"
echo "📝 View logs with: docker logs -f pipecat-$COMMAND"
echo "🛑 Stop with: docker stop pipecat-$COMMAND"
