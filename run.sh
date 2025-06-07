#!/bin/bash

# Stop on first error
set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup_env.sh first."
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Set environment variables
export FLASK_APP="src.app:app"
export FLASK_ENV="development"

# Run the application
echo "Starting development server..."
echo "Press Ctrl+C to stop the server"
echo ""

python -m flask run --host=0.0.0.0 --port=5000

# Keep the window open if there was an error
if [ $? -ne 0 ]; then
    echo -e "\nThe application exited with code $?"
    read -p "Press any key to continue..." -n1 -s
fi
