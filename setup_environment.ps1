# Setup script for AI-Docs
Write-Host "Setting up AI-Docs environment..." -ForegroundColor Cyan

# Activate virtual environment
if (-not (Test-Path .\venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
pip install sentence-transformers langchain-huggingface deep-translator

# Create necessary directories
$directories = @("uploads", "vector_store")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Place your documents in the 'uploads' folder"
Write-Host "2. Run: .\run_app.bat"
Write-Host "3. Open http://localhost:5000 in your browser"
Write-Host "4. Log in with admin/admin123"
