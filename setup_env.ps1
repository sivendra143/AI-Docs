<#
.SYNOPSIS
    Sets up the development environment for the PDF Chatbot application.
.DESCRIPTION
    This script helps set up the development environment by creating a virtual environment,
    installing dependencies, and setting up the database.
#>

# Stop on first error
$ErrorActionPreference = "Stop"

# Function to find Python executable
function Find-Python {
    try {
        # First try the py launcher
        $pyVersion = py --version 2>&1 | Out-String
        if ($pyVersion -match 'Python (\d+\.\d+\.\d+)') {
            $version = $matches[1]
            if ([version]$version -ge [version]"3.8.0") {
                return @{
                    Path = "py"
                    Version = $version
                }
            }
        }
        
        # Fall back to python3/python
        $pythonCommands = @('python3', 'python')
        foreach ($cmd in $pythonCommands) {
            try {
                $pythonPath = (Get-Command $cmd -ErrorAction Stop).Source
                $version = & $pythonPath -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
                
                if ($version -and [version]$version -ge [version]"3.8.0") {
                    return @{
                        Path = $pythonPath
                        Version = $version
                    }
                }
            } catch {
                # Command not found or version check failed
                continue
            }
        }
    } catch {
        # py launcher failed
    }
    
    return $null
}

# Check if Python is installed
$python = Find-Python
if (-not $python) {
    Write-Error "Python 3.8 or higher is required but not found. Please install Python 3.8+ and ensure it's in your PATH."
    Write-Host "You can download Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Python $($python.Version) at $($python.Path)" -ForegroundColor Green

# Create a virtual environment
$venvPath = ".\venv"
Write-Host "Creating virtual environment at $venvPath..." -ForegroundColor Cyan
& $python.Path -m venv $venvPath
if (-not $?) {
    Write-Error "Failed to create virtual environment"
    exit 1
}

# Activate the virtual environment
$activatePath = ".\venv\Scripts\Activate.ps1"
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path $activatePath)) {
    Write-Error "Failed to find virtual environment activation script at $activatePath"
    exit 1
}

try {
    & $activatePath
    if (-not $?) {
        throw "Activation failed"
    }
} catch {
    Write-Error "Failed to activate virtual environment: $_"
    exit 1
}

# Get the Python executable from the virtual environment
$venvPython = ".\venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Failed to find Python in virtual environment"
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
if (-not $?) {
    Write-Error "Failed to upgrade pip"
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install -r requirements.txt
if (-not $?) {
    Write-Error "Failed to install dependencies"
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from example..." -ForegroundColor Cyan
    if (Test-Path .env.example) {
        Copy-Item .env.example -Destination .env
        Write-Host "Created .env file. Please update it with your configuration." -ForegroundColor Yellow
    } else {
        Write-Warning ".env.example not found. Creating an empty .env file."
        New-Item -ItemType File -Path .env | Out-Null
    }
}

# Create necessary directories
$directories = @('uploads', 'instance', 'logs')
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Cyan
& $venvPython -m src.init_db
if ($?) {
    Write-Host "Database initialized successfully" -ForegroundColor Green
} else {
    Write-Warning "Database initialization completed with warnings"
}

Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "To activate the virtual environment, run:" -ForegroundColor Cyan
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "`nTo start the application, run:" -ForegroundColor Cyan
Write-Host "    .\run.ps1" -ForegroundColor White
$uploadsDir = "uploads"
if (-not (Test-Path $uploadsDir)) {
    Write-Host "Creating uploads directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $uploadsDir | Out-Null
}

# Create instance directory if it doesn't exist
$instanceDir = "instance"
if (-not (Test-Path $instanceDir)) {
    Write-Host "Creating instance directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $instanceDir | Out-Null
}

# Initialize the database
Write-Host "Initializing database..." -ForegroundColor Cyan
python -c "from src import create_app; from src.models import db; app = create_app('development'); app.app_context().push(); db.create_all()"

Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "To start the development server, run: .\run.ps1" -ForegroundColor Yellow
