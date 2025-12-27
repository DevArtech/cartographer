# ─────────────────────────────────────────────────────────────────────────────
# Cartographer Development Script (Windows PowerShell)
# Platform-agnostic script to run all services locally with hot reload
# ─────────────────────────────────────────────────────────────────────────────
#
# Usage:
#   .\dev.ps1              # Start all services
#   .\dev.ps1 start        # Start all services
#   .\dev.ps1 stop         # Stop all services
#   .\dev.ps1 status       # Check service status
#   .\dev.ps1 setup        # Install dependencies
#   .\dev.ps1 db           # Start only database services (postgres, redis)
#   .\dev.ps1 [service]    # Start specific service(s)
#
# ─────────────────────────────────────────────────────────────────────────────

param(
    [Parameter(Position=0)]
    [string]$Command = "start",
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Services
)

$ErrorActionPreference = "Stop"

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$Ports = @{
    backend = 8000
    health = 8001
    auth = 8002
    metrics = 8003
    assistant = 8004
    notification = 8005
    frontend = 5173
    postgres = 5432
    redis = 6379
}

$ServiceDirs = @{
    backend = "backend"
    health = "health-service"
    auth = "auth-service"
    metrics = "metrics-service"
    assistant = "assistant-service"
    notification = "notification-service"
    frontend = "frontend"
}

$PythonServices = @("backend", "health", "auth", "metrics", "assistant", "notification")

$LogDir = Join-Path $ScriptDir ".dev-logs"
$PidDir = Join-Path $ScriptDir ".dev-pids"

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

function Write-Log {
    param([string]$Message)
    Write-Host "[dev] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message
}

function Write-ServiceLog {
    param([string]$Service, [string]$Message)
    $colors = @{
        backend = "Blue"
        health = "Green"
        auth = "Magenta"
        metrics = "Cyan"
        assistant = "Yellow"
        notification = "Red"
        frontend = "White"
        postgres = "Green"
        redis = "Red"
    }
    Write-Host "[$Service] " -ForegroundColor $colors[$Service] -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[!] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Host "[error] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    return $connection.TcpTestSucceeded
}

function Wait-ForPort {
    param([int]$Port, [string]$Service, [int]$Timeout = 30)
    
    Write-ServiceLog $Service "Waiting for port $Port..."
    $count = 0
    while (-not (Test-Port $Port)) {
        Start-Sleep -Seconds 1
        $count++
        if ($count -ge $Timeout) {
            Write-Error "$Service failed to start (timeout waiting for port $Port)"
            return $false
        }
    }
    Write-Success "$Service is running on port $Port"
    return $true
}

# ═══════════════════════════════════════════════════════════════════════════════
# Environment Setup
# ═══════════════════════════════════════════════════════════════════════════════

function Initialize-Environment {
    # Load .env file if it exists
    $envFile = Join-Path $ScriptDir ".env"
    if (Test-Path $envFile) {
        Write-Log "Loading .env file"
        Get-Content $envFile | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    } else {
        Write-Warning "No .env file found. Copy .example.env to .env and configure it."
    }
    
    # Set defaults
    $defaults = @{
        POSTGRES_USER = "cartographer"
        POSTGRES_PASSWORD = "cartographer_secret"
        POSTGRES_DB = "cartographer"
        JWT_SECRET = "cartographer-dev-secret-change-in-production"
        CORS_ORIGINS = "*"
        APPLICATION_URL = "http://localhost:5173"
        HEALTH_SERVICE_URL = "http://localhost:8001"
        AUTH_SERVICE_URL = "http://localhost:8002"
        METRICS_SERVICE_URL = "http://localhost:8003"
        ASSISTANT_SERVICE_URL = "http://localhost:8004"
        NOTIFICATION_SERVICE_URL = "http://localhost:8005"
        BACKEND_SERVICE_URL = "http://localhost:8000"
        REDIS_URL = "redis://localhost:6379"
    }
    
    foreach ($key in $defaults.Keys) {
        if (-not [Environment]::GetEnvironmentVariable($key)) {
            [Environment]::SetEnvironmentVariable($key, $defaults[$key], "Process")
        }
    }
    
    $dbUrl = "postgresql+asyncpg://$($env:POSTGRES_USER):$($env:POSTGRES_PASSWORD)@localhost:5432/$($env:POSTGRES_DB)"
    if (-not $env:DATABASE_URL) {
        [Environment]::SetEnvironmentVariable("DATABASE_URL", $dbUrl, "Process")
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# Virtual Environment Management
# ═══════════════════════════════════════════════════════════════════════════════

function Initialize-Venv {
    param([string]$Service)
    
    $serviceDir = $ServiceDirs[$Service]
    $venvDir = Join-Path $ScriptDir $serviceDir ".venv"
    
    if (-not (Test-Path $venvDir)) {
        Write-ServiceLog $Service "Creating virtual environment..."
        python -m venv $venvDir
    }
    
    # Activate venv
    $activateScript = Join-Path $venvDir "Scripts" "Activate.ps1"
    & $activateScript
    
    # Install requirements if needed
    $reqFile = Join-Path $ScriptDir $serviceDir "requirements.txt"
    $markerFile = Join-Path $venvDir ".requirements-installed"
    
    if (-not (Test-Path $markerFile) -or ((Get-Item $reqFile).LastWriteTime -gt (Get-Item $markerFile).LastWriteTime)) {
        Write-ServiceLog $Service "Installing dependencies..."
        pip install --quiet --upgrade pip
        pip install --quiet -r $reqFile
        New-Item -Path $markerFile -ItemType File -Force | Out-Null
    }
    
    return $venvDir
}

function Initialize-Frontend {
    $frontendDir = Join-Path $ScriptDir "frontend"
    $nodeModules = Join-Path $frontendDir "node_modules"
    
    if (-not (Test-Path $nodeModules)) {
        Write-ServiceLog "frontend" "Installing dependencies..."
        Push-Location $frontendDir
        npm install
        Pop-Location
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# Service Management
# ═══════════════════════════════════════════════════════════════════════════════

function Start-Postgres {
    if (Test-Port $Ports.postgres) {
        Write-Success "PostgreSQL already running on port $($Ports.postgres)"
        return
    }
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker not available - please start PostgreSQL manually on port $($Ports.postgres)"
        return
    }
    
    Write-ServiceLog "postgres" "Starting PostgreSQL..."
    docker run -d --rm `
        --name cartographer-postgres-dev `
        -p 5432:5432 `
        -e POSTGRES_USER=$env:POSTGRES_USER `
        -e POSTGRES_PASSWORD=$env:POSTGRES_PASSWORD `
        -e POSTGRES_DB=$env:POSTGRES_DB `
        -v cartographer-postgres-dev:/var/lib/postgresql/data `
        postgres:16-alpine | Out-Null
    
    Wait-ForPort $Ports.postgres "postgres" 30
}

function Start-Redis {
    if (Test-Port $Ports.redis) {
        Write-Success "Redis already running on port $($Ports.redis)"
        return
    }
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker not available - please start Redis manually on port $($Ports.redis)"
        return
    }
    
    Write-ServiceLog "redis" "Starting Redis..."
    docker run -d --rm `
        --name cartographer-redis-dev `
        -p 6379:6379 `
        -v cartographer-redis-dev:/data `
        redis:7-alpine | Out-Null
    
    Wait-ForPort $Ports.redis "redis" 15
}

function Start-PythonService {
    param([string]$Service)
    
    $port = $Ports[$Service]
    $serviceDir = $ServiceDirs[$Service]
    
    if (Test-Port $port) {
        Write-Warning "$Service already running on port $port"
        return
    }
    
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
    New-Item -Path $PidDir -ItemType Directory -Force | Out-Null
    
    $venvDir = Initialize-Venv $Service
    
    Write-ServiceLog $Service "Starting on port $port with hot reload..."
    
    $workDir = Join-Path $ScriptDir $serviceDir
    $logFile = Join-Path $LogDir "$Service.log"
    $pidFile = Join-Path $PidDir "$Service.pid"
    
    $pythonExe = Join-Path $venvDir "Scripts" "python.exe"
    
    $process = Start-Process -FilePath $pythonExe -ArgumentList @(
        "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", $port,
        "--reload",
        "--reload-dir", "app"
    ) -WorkingDirectory $workDir -RedirectStandardOutput $logFile -RedirectStandardError $logFile -PassThru -NoNewWindow
    
    $process.Id | Out-File -FilePath $pidFile
    
    # Deactivate venv
    deactivate
    
    Wait-ForPort $port $Service 30
}

function Start-Frontend {
    $port = $Ports.frontend
    
    if (Test-Port $port) {
        Write-Warning "Frontend already running on port $port"
        return
    }
    
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
    New-Item -Path $PidDir -ItemType Directory -Force | Out-Null
    
    Initialize-Frontend
    
    Write-ServiceLog "frontend" "Starting Vite dev server on port $port..."
    
    $workDir = Join-Path $ScriptDir "frontend"
    $logFile = Join-Path $LogDir "frontend.log"
    $pidFile = Join-Path $PidDir "frontend.pid"
    
    $process = Start-Process -FilePath "npm" -ArgumentList @("run", "dev") `
        -WorkingDirectory $workDir -RedirectStandardOutput $logFile -RedirectStandardError $logFile -PassThru -NoNewWindow
    
    $process.Id | Out-File -FilePath $pidFile
    
    Wait-ForPort $port "frontend" 30
}

function Stop-Service {
    param([string]$Service)
    
    $pidFile = Join-Path $PidDir "$Service.pid"
    
    if (Test-Path $pidFile) {
        $pid = Get-Content $pidFile
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-ServiceLog $Service "Stopping (PID $pid)..."
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
        Remove-Item $pidFile -Force
    }
}

function Stop-DockerService {
    param([string]$Container)
    
    $running = docker ps -q -f name=$Container 2>$null
    if ($running) {
        Write-Log "Stopping $Container..."
        docker stop $Container 2>$null | Out-Null
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-Setup {
    Write-Log "Setting up development environment..."
    
    Initialize-Environment
    
    foreach ($service in $PythonServices) {
        Initialize-Venv $service | Out-Null
        deactivate
    }
    
    Initialize-Frontend
    
    Write-Success "Development environment ready!"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Copy .example.env to .env and configure your settings"
    Write-Host "  2. Run .\dev.ps1 to start all services"
}

function Invoke-Start {
    param([string[]]$ServiceList)
    
    Initialize-Environment
    
    if (-not $ServiceList -or $ServiceList.Count -eq 0) {
        $ServiceList = @("postgres", "redis", "health", "auth", "metrics", "assistant", "notification", "backend", "frontend")
    }
    
    Write-Log "Starting services: $($ServiceList -join ', ')"
    Write-Host ""
    
    foreach ($service in $ServiceList) {
        switch ($service) {
            "postgres" { Start-Postgres }
            "redis" { Start-Redis }
            "frontend" { Start-Frontend }
            { $_ -in $PythonServices } { Start-PythonService $service }
            "db" { Start-Postgres; Start-Redis }
            default { Write-Error "Unknown service: $service" }
        }
    }
    
    Write-Host ""
    Write-Success "All services started!"
    Write-Host ""
    Write-Host "Service URLs:"
    Write-Host "  Frontend:     http://localhost:$($Ports.frontend)" -ForegroundColor Cyan
    Write-Host "  Backend:      http://localhost:$($Ports.backend)" -ForegroundColor Blue
    Write-Host "  Auth:         http://localhost:$($Ports.auth)" -ForegroundColor Magenta
    Write-Host "  Health:       http://localhost:$($Ports.health)" -ForegroundColor Green
    Write-Host "  Metrics:      http://localhost:$($Ports.metrics)" -ForegroundColor Cyan
    Write-Host "  Assistant:    http://localhost:$($Ports.assistant)" -ForegroundColor Yellow
    Write-Host "  Notification: http://localhost:$($Ports.notification)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Logs: $LogDir"
    Write-Host "Press Ctrl+C to stop all services"
}

function Invoke-Stop {
    Write-Log "Stopping all services..."
    
    foreach ($service in $PythonServices) {
        Stop-Service $service
    }
    Stop-Service "frontend"
    
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Stop-DockerService "cartographer-postgres-dev"
        Stop-DockerService "cartographer-redis-dev"
    }
    
    Write-Success "All services stopped"
}

function Invoke-Status {
    Write-Host ""
    Write-Host "Service Status" -ForegroundColor White
    Write-Host "─────────────────────────────────────"
    
    $allServices = @("postgres", "redis", "backend", "frontend", "health", "auth", "metrics", "assistant", "notification")
    
    foreach ($service in $allServices) {
        $port = $Ports[$service]
        if (Test-Port $port) {
            Write-Host "$service" -ForegroundColor Cyan -NoNewline
            Write-Host ": " -NoNewline
            Write-Host "Running" -ForegroundColor Green -NoNewline
            Write-Host " (port $port)"
        } else {
            Write-Host "$service" -ForegroundColor Cyan -NoNewline
            Write-Host ": " -NoNewline
            Write-Host "Stopped" -ForegroundColor Red
        }
    }
    Write-Host ""
}

function Show-Help {
    @"
Cartographer Development Script (Windows PowerShell)

Usage:
  .\dev.ps1 [command] [services...]

Commands:
  start [services...]  Start services (default: all)
  stop                 Stop all services
  status               Show service status
  setup                Install dependencies
  db                   Start only database services
  help                 Show this help

Services:
  backend              Main API gateway (port 8000)
  frontend             Vue.js frontend (port 5173)
  auth                 Authentication service (port 8002)
  health               Health check service (port 8001)
  metrics              Metrics service (port 8003)
  assistant            AI assistant service (port 8004)
  notification         Notification service (port 8005)
  postgres             PostgreSQL database (port 5432)
  redis                Redis cache (port 6379)

Examples:
  .\dev.ps1                    # Start all services
  .\dev.ps1 backend frontend   # Start only backend and frontend
  .\dev.ps1 db                 # Start only postgres and redis
  .\dev.ps1 status             # Check what's running
  .\dev.ps1 stop               # Stop everything
"@
}

# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

switch ($Command.ToLower()) {
    "start"   { Invoke-Start $Services }
    "stop"    { Invoke-Stop }
    "status"  { Invoke-Status }
    "setup"   { Invoke-Setup }
    "db"      { Initialize-Environment; Start-Postgres; Start-Redis }
    { $_ -in @("help", "-h", "--help") } { Show-Help }
    { $_ -in @("backend", "frontend", "health", "auth", "metrics", "assistant", "notification") } {
        Invoke-Start @($Command) + $Services
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}

