#!/bin/bash

# Stop on first error
set -e

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3.8 or higher is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "Python 3.8 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

# Create uploads directory if it doesn't exist
UPLOADS_DIR="uploads"
if [ ! -d "$UPLOADS_DIR" ]; then
    echo "Creating uploads directory..."
    mkdir -p "$UPLOADS_DIR"
fi

# Create instance directory if it doesn't exist
INSTANCE_DIR="instance"
if [ ! -d "$INSTANCE_DIR" ]; then
    echo "Creating instance directory..."
    mkdir -p "$INSTANCE_DIR"
fi

# Initialize the database
echo "Initializing database..."
python -c "from src import create_app; from src.models import db; app = create_app('development'); app.app_context().push(); db.create_all()"

echo -e "\nSetup completed successfully!"
echo -e "To start the development server, run: ./run.sh"

# Make the run script executable
chmod +x run.sh
