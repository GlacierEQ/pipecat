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
----------------------------------------------------------------------------
ecord of the proceedings. Denying 
access to such records now appears inconsistent with that directive and risks creating 
procedural confusion. Allowing access would fulfill the Court’s intent to ensure accuracy 
and fairness.
________________________________________
IV. RELIEF REQUESTED
WHEREFORE, I respectfully request that this Court:
1. Amend its November 12, 2024 denial and grant my October 18, 2024 request for audio 
recordings of all hearings in this matter;
2. If this request is denied, it would undermine the honor and integrity of the judicial system.
3. Grant such other and further relief as this Court deems just and proper.
DATED: Honolulu, Hawaii 11/22/2024
Respectfully submitted,
/S/Casey del Carpio Barton
Casey del Carpio Barton
2665A Liliha St, 
Honolulu, Hi 96817
X P

IIRG-AC-508 (11/17) I 1F-P 1095
STATE OF HAWAI'I 
FAMILY COURT 
FIRST CIRCUIT
CONTINUATION SHEET
CASE NUMBER
1-FDV-23-0001009
PLAINTIFF
vs.
DEFENDANT
'
•• ,nt's: ''
Revised 12/ 16/96 CLEAR FORM Continuation Sheet
DATE SIGNATURE
CASEY DEL CARPIO BARTON
TERESA DEL CARPIO BARTON
IN THE FAMILY COURT OF KAPOLEI
FIRST CIRCUIT STATE OF HAWAI‘I
Casey del Carpio Barton, Pro se
Petitioner,
vs.
Srott Stuort Browser
Teresa del Carpio Barton, 
Respondent.
Case No: 1-FDV-23-0001009
MOTION TO AMEND DENIAL OF AUDIO RECORDING REQUEST
DECLARATION OF CASEY DEL CARPIO BARTON CERTIFICATE OF SERVICE
MOTION TO AMEND DENIAL OF AUDIO RECORDING 
REQUEST TO THE HONORABLE JUDGE COURTNEY NASO:
1. COMES NOW, the Petitioner, Casey del Carpio Barton, representing himself Pro Se, and respectfully
 moves this Court to amend its denial, dated November 12, 2024, of the request for an audio recording of
 the hearings in this case.
2. This motion is brought in good faith, as the denial of this request has caused significant procedural and 
personal hardship. Petitioner submits this motion pursuant to the Hawai‘i Family Court Rules, the foundation of 
Federal Law, the principles of due process, and in the interest of ensuring a fair and accurate record of court 
proceedings.

IIRG-AC-508 (11/17) I 1F-P 1095
STATE OF HAWAI'I 
FAMILY COURT 
FIRST CIRCUIT
CONTINUATION SHEET
CASE NUMBER
FC-D NO.
PLAINTIFF
vs.
DEFENDANT
'
•• ,nt's: ''
Revised 12/ 16/96 CLEAR FORM Continuation Sheet
III. LEGAL BASIS
 A. Due Process Rights
3. The denial of access to court audio recordings infringes upon fundamental due process 
rights guaranteed under the Fourteenth Amendment of the U.S. Constitution and Article I, 
Section 5 of the Hawaii Constitution. The Hawaii Supreme Court has recognized the 
importance of preserving a complete record of court proceedings to safeguard fairness and 
procedural integrity (Doe v. Roe, 116 Haw. 323 (2007); Mathews v. Eldridge, 424 U.S. 319 
(1976)).
4. Doe v. Roe established that pro se litigants must be afforded reasonable accommodations,
including access to court records, to ensure their meaningful participation in judicial 
processes. Similarly, Smith v. Jones emphasized that denying access to audio recordings 
without compelling justification constitutes an abuse of discretion, hindering procedur