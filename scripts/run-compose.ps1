<#
.SYNOPSIS
    Enhanced script to run Pipecat in different Docker Compose environments
.DESCRIPTION
    This script provides easy management of different Docker Compose environments for Pipecat
.PARAMETER Environment
    Environment to use: dev, prod, or monitor
.PARAMETER Service
    The service(s) to target
.PARAMETER Action
    Action to perform: up, down, restart, logs, build, or exec
#>

param(
    [ValidateSet("dev", "prod", "monitor")]
    [string]$Environment = "dev",
    
    [string]$Service = "app",
    
    [ValidateSet("up", "down", "restart", "logs", "build", "exec")]
    [string]$Action = "up"
)

# Display banner
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                     PIPECAT DOCKER RUNNER                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Check for Docker Compose
$ComposeCommand = $null
if (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
    $ComposeCommand = "docker-compose"
}
elseif (Get-Command "docker" -ErrorAction SilentlyContinue) {
    # Check if docker compose is available
    try {
        docker compose version | Out-Null
        $ComposeCommand = "docker compose"
    }
    catch {
        Write-Host "❌ Error: Docker Compose not found. Please install Docker Compose." -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "❌ Error: Docker not found. Please install Docker." -ForegroundColor Red
    exit 1
}

# Set environment-specific compose files
switch ($Environment) {
    "dev" {
        $ComposeFiles = "-f docker-compose.yml -f docker-compose.dev.yml"
        $EnvDesc = "Development"
    }
    "prod" {
        $ComposeFiles = "-f docker-compose.yml -f docker-compose.prod.yml"
        $EnvDesc = "Production"
    }
    "monitor" {
        $ComposeFiles = "-f docker-compose.yml -f docker-compose.prod.yml"
        $Service = "app prometheus grafana"
        $EnvDesc = "Production with Monitoring"
    }
}

# Execute the command
switch ($Action) {
    "up" {
        Write-Host "🚀 Starting $EnvDesc environment..." -ForegroundColor Green
        Invoke-Expression "$ComposeCommand $ComposeFiles up -d $Service"
        Write-Host "✅ Containers started!" -ForegroundColor Green
        
        # Show service access information
        switch ($Environment) {
            "dev" {
                Write-Host "📊 Dashboard available at: http://localhost:8080" -ForegroundColor Cyan
                Write-Host "🔌 API available at: http://localhost:8000" -ForegroundColor Cyan
                Write-Host "🐞 Debug port: 5678" -ForegroundColor Cyan
            }
            "prod" {
                Write-Host "📊 Dashboard available at: http://localhost:8080" -ForegroundColor Cyan
                Write-Host "🔌 API available at: http://localhost:8000" -ForegroundColor Cyan
            }
            "monitor" {
                Write-Host "📊 Dashboard available at: http://localhost:8080" -ForegroundColor Cyan
                Write-Host "📊 Prometheus available at: http://localhost:9090" -ForegroundColor Cyan
                Write-Host "📊 Grafana available at: http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
            }
        }
    }
    "down" {
        Write-Host "🛑 Stopping containers..." -ForegroundColor Yellow
        Invoke-Expression "$ComposeCommand $ComposeFiles down"
        Write-Host "✅ Containers stopped!" -ForegroundColor Green
    }
    "restart" {
        Write-Host "🔄 Restarting containers..." -ForegroundColor Yellow
        Invoke-Expression "$ComposeCommand $ComposeFiles restart $Service"
        Write-Host "✅ Containers restarted!" -ForegroundColor Green
    }
    "logs" {
        Write-Host "📋 Showing logs for $Service..." -ForegroundColor Cyan
        Invoke-Expression "$ComposeCommand $ComposeFiles logs -f $Service"
    }
    "build" {
        Write-Host "🛠️ Building images..." -ForegroundColor Yellow
        Invoke-Expression "$ComposeCommand $ComposeFiles build $Service"
        Write-Host "✅ Build complete!" -ForegroundColor Green
    }
    "exec" {
        Write-Host "🧪 Executing shell in $Service container..." -ForegroundColor Cyan
        Invoke-Expression "$ComposeCommand $ComposeFiles exec $Service /bin/bash"
    }
}

Write-Host "✅ Operation complete!" -ForegroundColor Green
