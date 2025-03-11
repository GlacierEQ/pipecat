# This script attempts to build and run the Docker container using WSL2

# Check if WSL is installed
$wslCheck = wsl --list
if ($LASTEXITCODE -ne 0) {
    Write-Host "WSL is not installed or enabled on this system" -ForegroundColor Red
    Write-Host "Please install WSL2 by running 'wsl --install' in an admin PowerShell" -ForegroundColor Yellow
    exit 1
}

# Navigate to project directory in WSL
$projectPath = $PWD.Path.Replace("\", "/").Replace("C:", "/mnt/c")
Write-Host "Building Docker image using WSL at path $projectPath" -ForegroundColor Cyan

# Build and run with WSL
wsl -e bash -c "cd $projectPath && docker build -t pipecat-app ."
if ($LASTEXITCODE -eq 0) {
    Write-Host "Docker image built successfully" -ForegroundColor Green
    Write-Host "Starting container..." -ForegroundColor Cyan
    wsl -e bash -c "cd $projectPath && docker run -d -p 8000:8000 pipecat-app"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Container started successfully. Access at http://localhost:8000" -ForegroundColor Green
    } else {
        Write-Host "Failed to start container" -ForegroundColor Red
    }
} else {
    Write-Host "Failed to build Docker image" -ForegroundColor Red
}
