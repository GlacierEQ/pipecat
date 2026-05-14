#!/bin/bash
# Enhanced script to run Pipecat in different Docker Compose environments

set -e

# Configuration
COMPOSE_PROJECT_NAME="pipecat"
ENV=${1:-dev}  # Default to dev environment
SERVICE=${2:-app}  # Default to app service
ACTION=${3:-up}  # Default action is to start containers

# Display ASCII banner for visual indication
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                     PIPECAT DOCKER RUNNER                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Check for Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Error: Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Set environment-specific compose files
case "$ENV" in
    dev)
        COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
        ENV_DESC="Development"
        ;;
    prod)
        COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
        ENV_DESC="Production"
        ;;
    monitor)
        COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
        SERVICE="app prometheus grafana"
        ENV_DESC="Production with Monitoring"
        ;;
    *)
        echo "❌ Invalid environment: $ENV"
        echo "Valid options: dev, prod, monitor"
        exit 1
        ;;
esac

# Execute the command
case "$ACTION" in
    up)
        echo "🚀 Starting $ENV_DESC environment..."
        $COMPOSE_CMD $COMPOSE_FILES up -d $SERVICE
        echo "✅ Containers started!"
        
        # Show service access information
        if [[ "$ENV" == "dev" ]]; then
            echo "📊 Dashboard available at: http://localhost:8080"
            echo "🔌 API available at: http://localhost:8000"
            echo "🐞 Debug port: 5678"
        elif [[ "$ENV" == "prod" ]]; then
            echo "📊 Dashboard available at: http://localhost:8080"
            echo "🔌 API available at: http://localhost:8000"
        elif [[ "$ENV" == "monitor" ]]; then
            echo "📊 Dashboard available at: http://localhost:8080"
            echo "📊 Prometheus available at: http://localhost:9090"
            echo "📊 Grafana available at: http://localhost:3000 (admin/admin)"
        fi
        ;;
    down)
        echo "🛑 Stopping containers..."
        $COMPOSE_CMD $COMPOSE_FILES down
        echo "✅ Containers stopped!"
        ;;
    restart)
        echo "🔄 Restarting containers..."
        $COMPOSE_CMD $COMPOSE_FILES restart $SERVICE
        echo "✅ Containers restarted!"
        ;;
    logs)
        echo "📋 Showing logs for $SERVICE..."
        $COMPOSE_CMD $COMPOSE_FILES logs -f $SERVICE
        ;;
    build)
        echo "🛠️ Building images..."
        $COMPOSE_CMD $COMPOSE_FILES build $SERVICE
        echo "✅ Build complete!"
        ;;
    exec)
        echo "🧪 Executing shell in $SERVICE container..."
        $COMPOSE_CMD $COMPOSE_FILES exec $SERVICE /bin/bash
        ;;
    *)
        echo "❌ Invalid action: $ACTION"
        echo "Valid actions: up, down, restart, logs, build, exec"
        exit 1
        ;;
esac

echo "✅ Operation complete!"
