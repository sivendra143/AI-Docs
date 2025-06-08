# Run this script to start the application with cleanup
Write-Host "=== AI-Docs Application Startup ===" -ForegroundColor Cyan
Write-Host "Ensuring all dependencies are installed..." -ForegroundColor Yellow

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found. Please run setup_environment.ps1 first" -ForegroundColor Red
    exit 1
}

# Install required packages if not already installed
$required_packages = @("sentence-transformers", "langchain-huggingface", "deep-translator")
foreach ($pkg in $required_packages) {
    $installed = pip show $pkg 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing $pkg..." -ForegroundColor Yellow
        pip install $pkg
    }
}

# Clean up old data
Write-Host "`nCleaning up previous data..." -ForegroundColor Yellow
if (Test-Path vector_store) {
    Remove-Item -Recurse -Force vector_store
    Write-Host "Removed old vector store" -ForegroundColor Green
}

# Create new directories
$directories = @("vector_store", "uploads")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Process documents if any exist
$has_documents = (Get-ChildItem -Path ".\uploads\*" -Include @("*.pdf", "*.docx", "*.txt", "*.csv") -Recurse).Count -gt 0
if ($has_documents) {
    Write-Host "`nProcessing documents..." -ForegroundColor Yellow
    try {
        python -c "from src.document_processor import DocumentProcessor; processor = DocumentProcessor(docs_folder='./uploads/'); processor.process_documents(); print('Documents processed successfully!')"
        Write-Host "Documents processed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Error processing documents: $_" -ForegroundColor Red
    }
} else {
    Write-Host "`nNo documents found in 'uploads' folder. Please add documents and restart the application." -ForegroundColor Yellow
}

# Start the application
Write-Host "`n=== Starting Application ===" -ForegroundColor Cyan
Write-Host "Server will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host "==========================`n" -ForegroundColor Cyan

try {
    # Run the application
    python -m src.wsgi
} catch {
    Write-Host "Error starting application: $_" -ForegroundColor Red
}

# Keep the window open after the app stops
Write-Host "`nApplication stopped. Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
