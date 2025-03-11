Write-Host "Checking Docker installation..." -ForegroundColor Cyan

# Check if Docker is installed and available in PATH
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $dockerPath) {
    Write-Host "Docker is not installed or not in your PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    
    # Check if Docker Desktop is installed but not in PATH
    $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktopPath) {
        Write-Host "Docker Desktop seems to be installed but not running or not in PATH" -ForegroundColor Yellow
        Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "Docker is installed at: $($dockerPath.Source)" -ForegroundColor Green
Write-Host "Docker version: " -ForegroundColor Green -NoNewline
docker version

# Check if Docker daemon is running
try {
    $info = docker info 2>$null
    Write-Host "Docker daemon is running properly" -ForegroundColor Green
} catch {
    Write-Host "Docker daemon doesn't seem to be running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nDocker is properly installed and running. You can proceed with building your container." -ForegroundColor Green
