<#
.SYNOPSIS
    Automated script to build and run pipecat in Docker
.DESCRIPTION
    Builds and runs the Pipecat Docker container with specified parameters
.PARAMETER Mode
    Mode: 'prod' or 'dev'
.PARAMETER Command
    Pipecat command to run: 'dashboard', 'api', etc.
.PARAMETER Host
    Host to bind to, defaults to '0.0.0.0'
.PARAMETER Port
    Port to expose, defaults to 8080
#>

param(
    [string]$Mode = "prod",
    [string]$Command = "dashboard",
    [string]$Host = "0.0.0.0", 
    [string]$Port = "8080"
)

# Default configuration
$ImageName = "pipecat"
$ContainerName = "pipecat-server"

Write-Host "🚀 Starting Pipecat Docker automation..." -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker info | Out-Null
}
catch {
    Write-Host "❌ Error: Docker is not installed or not running" -ForegroundColor Red
    exit 1
}

# Determine which Dockerfile to use based on mode
if ($Mode -eq "dev") {
    $Dockerfile = "docker/Dockerfile.dev"
    $ImageTag = "dev"
    $ContainerName = "pipecat-dev"
    $AdditionalArgs = "--volume ${PWD}:/workspaces/pipecat"
}
else {
    $Dockerfile = "docker/Dockerfile" 
    $ImageTag = "latest"
    $ContainerName = "pipecat-server"
    $AdditionalArgs = ""
}

# Build the Docker image
Write-Host "🔧 Building Docker image..." -ForegroundColor Yellow
docker build -t "${ImageName}:${ImageTag}" -f $Dockerfile .

# Check if we already have a container with this name
$existingContainer = docker ps -a --filter "name=$ContainerName" --format '{{.Names}}'
if ($existingContainer -eq $ContainerName) {
    Write-Host "🧹 Removing existing container..." -ForegroundColor Yellow
    docker rm -f $ContainerName
}

# Create and run the container
Write-Host "🚀 Starting container with command: $Command --host $Host --port $Port" -ForegroundColor Green
$dockerCmd = "docker run --name $ContainerName -p ${Port}:${Port} -e 'PIPECAT_CACHE_DIR=/app/cache' -v pipecat_cache:/app/cache $AdditionalArgs -d ${ImageName}:${ImageTag} $Command --host $Host --port $Port"
Invoke-Expression $dockerCmd

Write-Host "✅ Container started! Access the service at http://localhost:$Port" -ForegroundColor Green
Write-Host "📖 View logs with: docker logs -f $ContainerName" -ForegroundColor Cyan
Write-Host "🛑 Stop with: docker stop $ContainerName" -ForegroundColor Cyan
