<#
.SYNOPSIS
    Starts the PDF Chatbot application in development mode.
.DESCRIPTION
    This script activates the virtual environment and starts the Flask development server
    with WebSocket support.
#>

# Stop on first error
$ErrorActionPreference = "Stop"

# Function to display a header
function Show-Header {
    Clear-Host
    Write-Host "=== PDF Chatbot Application ===" -ForegroundColor Cyan
    Write-Host "Starting development server...`n" -ForegroundColor White
}

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    return (Get-Command $command -ErrorAction SilentlyContinue) -ne $null
}

# Display header
Show-Header

# Check if virtual environment exists
$venvPath = ".\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found." -ForegroundColor Red
    $setup = Read-Host "Run setup script now? (Y/N)"
    if ($setup -eq 'Y' -or $setup -eq 'y') {
        .\setup_env.ps1
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    } else {
        Write-Host "Please run .\setup_env.ps1 first." -ForegroundColor Yellow
        exit 1
    }
}

# Activate the virtual environment
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Error "Virtual environment activation script not found at $activateScript"
    exit 1
}

try {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & $activateScript
    if (-not $?) {
        throw "Failed to activate virtual environment"
    }
} catch {
    Write-Error "Error activating virtual environment: $_"
    exit 1
}

# Set environment variables
$env:FLASK_APP = "src.app:create_app()"
$env:FLASK_ENV = "development"
$env:PYTHONUNBUFFERED = "1"

# Use the system Python launcher (py) with virtual environment
$pythonExe = "py"
if (-not (Get-Command $pythonExe -ErrorAction SilentlyContinue)) {
    Write-Error "Python launcher (py) not found"
    exit 1
}

# Activate the virtual environment for the current session
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
}

# Display server information
$ipAddress = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'IPv4' -and $_.PrefixOrigin -eq 'Dhcp' } | Select-Object -ExpandProperty IPAddress | Select-Object -First 1)
$port = 5000

Write-Host "`nStarting development server..." -ForegroundColor Cyan
Write-Host "Local:        http://localhost:$port" -ForegroundColor White
if ($ipAddress) {
    Write-Host "Network:      http://$($ipAddress):$port" -ForegroundColor White
}
Write-Host "Environment:  $($env:FLASK_ENV)" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

# Run the application
try {
    # Use the Python from the virtual environment
    & $pythonExe -m flask run --host=0.0.0.0 --port=$port --debugger --reload
    $exitCode = $LASTEXITCODE
} catch {
    Write-Error "Error running the application: $_"
    $exitCode = 1
}

# Keep the window open if there was an error
if ($exitCode -ne 0) {
    Write-Host "`nThe application exited with code $exitCode" -ForegroundColor Red
    if (-not $env:CI -and $Host.Name -match "console") {
        Write-Host "`nPress any key to exit..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    }
    exit $exitCode
}
