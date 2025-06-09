#!/bin/bash

# AI Document Chat - Setup Script for Linux/macOS
# This script helps set up the development environment for the AI Document Chat application.
# It creates necessary directories, sets up a virtual environment, and installs dependencies.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Constants
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
CONFIG_EXAMPLE="config.example.json"
CONFIG_FILE="config.json"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    echo -e "${BLUE}[1/5] Checking Python version...${NC}"
    
    if ! command_exists python3; then
        echo -e "${RED}Python 3 is not installed. Please install Python 3.10 or higher and try again.${NC}"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    REQUIRED_VERSION="3.10.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
        echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"
        return 0
    else
        echo -e "${RED}Python $REQUIRED_VERSION or higher is required. Found Python $PYTHON_VERSION${NC}"
        return 1
    fi
}

# Function to create and activate virtual environment
setup_virtualenv() {
    echo -e "\n${BLUE}[2/5] Setting up virtual environment...${NC}"
    
    if [ -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Virtual environment already exists at $VENV_DIR${NC}"
    else
        echo -e "${BLUE}Creating virtual environment in $VENV_DIR...${NC}"
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate the virtual environment
    if [ -f "$VENV_DIR/bin/activate" ]; then
        echo -e "${BLUE}Activating virtual environment...${NC}"
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${RED}Failed to find virtual environment activation script${NC}"
        return 1
    fi
    
    return 0
}

# Function to install dependencies
install_dependencies() {
    echo -e "\n${BLUE}[3/5] Installing dependencies...${NC}"
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${RED}Requirements file not found: $REQUIREMENTS_FILE${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Upgrading pip...${NC}"
    python3 -m pip install --upgrade pip
    
    echo -e "${BLUE}Installing dependencies from $REQUIREMENTS_FILE...${NC}"
    python3 -m pip install -r "$REQUIREMENTS_FILE"
    
    # Install additional development tools
    echo -e "${BLUE}Installing additional development tools...${NC}"
    python3 -m pip install black flake8 pytest pytest-cov pre-commit
    
    return $?
}

# Function to initialize configuration
initialize_config() {
    echo -e "\n${BLUE}[4/5] Initializing configuration...${NC}"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "$CONFIG_EXAMPLE" ]; then
            echo -e "${BLUE}Creating configuration file from example...${NC}"
            cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
            echo -e "${YELLOW}Please edit $CONFIG_FILE to configure the application${NC}"
        else
            echo -e "${RED}No configuration example file found. Please create $CONFIG_FILE manually.${NC}"
        fi
    else
        echo -e "${GREEN}Configuration file already exists: $CONFIG_FILE${NC}"
    fi
}

# Function to create necessary directories
create_directories() {
    echo -e "\n${BLUE}[5/5] Setting up directories...${NC}"
    
    mkdir -p "./docs"
    mkdir -p "./vector_store"
    mkdir -p "./uploads"
    
    echo -e "${GREEN}Created necessary directories${NC}"
}

# Main execution
echo -e "\n${BLUE}==========================================================${NC}"
echo -e "${BLUE}           AI Document Chat - Setup Script${NC}"
echo -e "${BLUE}==========================================================${NC}\n"

# Check Python version
if ! check_python_version; then
    exit 1
fi

# Create necessary directories
create_directories

# Set up virtual environment
if ! setup_virtualenv; then
    exit 1
fi

# Install dependencies
if ! install_dependencies; then
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi

# Initialize configuration
initialize_config

# Success message
echo -e "\n${GREEN}==========================================================${NC}"
echo -e "${GREEN}           Setup completed successfully!${NC}"
echo -e "${GREEN}==========================================================${NC}\n"

echo -e "${BLUE}To activate the virtual environment, run:${NC}"
echo -e "  source $VENV_DIR/bin/activate\n"

echo -e "${BLUE}To start the application, run:${NC}"
echo -e "  python run_app.py\n"

echo -e "${BLUE}Open your browser and navigate to: http://localhost:5000${NC}\n"

# Ask if user wants to start the application
read -p "Would you like to start the application now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Starting AI Document Chat...${NC}"
    python3 run_app.py
fi
