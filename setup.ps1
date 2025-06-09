<#
.SYNOPSIS
    Setup script for AI Document Chat application
.DESCRIPTION
    This script helps set up the development environment for the AI Document Chat application.
    It creates necessary directories, sets up a virtual environment, and installs dependencies.
#>

# Stop on first error
$ErrorActionPreference = "Stop"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Constants
$VENV_DIR = ".venv"
$REQUIREMENTS_FILE = "requirements.txt"
$CONFIG_EXAMPLE = "config.example.json"
$CONFIG_FILE = "config.json"

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Function to create directory if it doesn't exist
function Ensure-DirectoryExists {
    param($path)
    if (-not (Test-Path -Path $path)) {
        Write-Host "Creating directory: $path" -ForegroundColor Cyan
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

# Function to check Python version
function Test-PythonVersion {
    $pythonVersion = python --version 2>&1 | Select-String -Pattern "Python (\d+\.\d+)"
    if (-not $pythonVersion) {
        Write-Host "Python is not installed or not in PATH" -ForegroundColor Red
        return $false
    }
    
    $version = [version]($pythonVersion.Matches.Groups[1].Value)
    $requiredVersion = [version]"3.10.0"
    
    if ($version -lt $requiredVersion) {
        Write-Host "Python $requiredVersion or higher is required. Found Python $version" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Found Python $version" -ForegroundColor Green
    return $true
}

# Function to create and activate virtual environment
function Initialize-Venv {
    param($venvDir)
    
    if (Test-Path -Path $venvDir) {
        Write-Host "Virtual environment already exists at $venvDir" -ForegroundColor Yellow
    } else {
        Write-Host "Creating virtual environment in $venvDir..." -ForegroundColor Cyan
        python -m venv $venvDir
    }
    
    # Activate the virtual environment
    $activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        Write-Host "Activating virtual environment..." -ForegroundColor Cyan
        . $activateScript
    } else {
        Write-Host "Failed to find virtual environment activation script" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Function to install dependencies
function Install-Dependencies {
    param($requirementsFile)
    
    if (-not (Test-Path -Path $requirementsFile)) {
        Write-Host "Requirements file not found: $requirementsFile" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Upgrading pip..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    
    Write-Host "Installing dependencies from $requirementsFile..." -ForegroundColor Cyan
    python -m pip install -r $requirementsFile
    
    # Install additional packages that might be needed
    Write-Host "Installing additional development tools..." -ForegroundColor Cyan
    python -m pip install black flake8 pytest pytest-cov pre-commit
    
    return $?
}

# Function to initialize configuration
function Initialize-Configuration {
    if (-not (Test-Path -Path $CONFIG_FILE)) {
        if (Test-Path -Path $CONFIG_EXAMPLE) {
            Write-Host "Creating configuration file from example..." -ForegroundColor Cyan
            Copy-Item -Path $CONFIG_EXAMPLE -Destination $CONFIG_FILE
            Write-Host "Please edit $CONFIG_FILE to configure the application" -ForegroundColor Yellow
        } else {
            Write-Host "No configuration example file found. Please create $CONFIG_FILE manually." -ForegroundColor Red
        }
    } else {
        Write-Host "Configuration file already exists: $CONFIG_FILE" -ForegroundColor Green
    }
}

# Main execution
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "AI Document Chat - Setup Script".PadLeft(45) -ForegroundColor Cyan
Write-Host ("=" * 60) + "`n" -ForegroundColor Cyan

# Check Python version
Write-Host "[1/5] Checking Python version..." -ForegroundColor Cyan
if (-not (Test-PythonVersion)) {
    Write-Host "Please install Python 3.10 or higher and try again." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "`n[2/5] Setting up directories..." -ForegroundColor Cyan
Ensure-DirectoryExists "./docs"
Ensure-DirectoryExists "./vector_store"
Ensure-DirectoryExists "./uploads"

# Set up virtual environment
Write-Host "`n[3/5] Setting up virtual environment..." -ForegroundColor Cyan
if (-not (Initialize-Venv -venvDir $VENV_DIR)) {
    exit 1
}

# Install dependencies
Write-Host "`n[4/5] Installing dependencies..." -ForegroundColor Cyan
if (-not (Install-Dependencies -requirementsFile $REQUIREMENTS_FILE)) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Initialize configuration
Write-Host "`n[5/5] Initializing configuration..." -ForegroundColor Cyan
Initialize-Configuration

# Success message
Write-Host "`n" + ("=" * 60) -ForegroundColor Green
Write-Host "Setup completed successfully!".PadLeft(38) -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green

Write-Host "`nTo activate the virtual environment, run:" -ForegroundColor Cyan
Write-Host "  .\$VENV_DIR\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "`nTo start the application, run:" -ForegroundColor Cyan
Write-Host "  python run_app.py" -ForegroundColor White
Write-Host "`nOpen your browser and navigate to: http://localhost:5000" -ForegroundColor Cyan

# Check if we should start the application
$startApp = Read-Host -Prompt "`nWould you like to start the application now? (y/n)"
if ($startApp -eq 'y' -or $startApp -eq 'Y') {
    Write-Host "`nStarting AI Document Chat..." -ForegroundColor Cyan
    python run_app.py
}
