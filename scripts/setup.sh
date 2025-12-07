#!/bin/bash

# Setup script for Nexora project
# This script handles the initial setup of the project environment.

set -euo pipefail

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
BACKEND_DIR="$PROJECT_ROOT/src"
FRONTEND_DIR="$PROJECT_ROOT/web-frontend"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# --- Utility Functions ---

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to ensure Python virtual environment is set up
ensure_venv() {
  if [ ! -d "$VENV_PATH" ]; then
    echo -e "${BLUE}Creating Python virtual environment at $VENV_PATH...${NC}"
    python3 -m venv "$VENV_PATH"
  fi
  source "$VENV_PATH/bin/activate"
  echo -e "${GREEN}Virtual environment activated.${NC}"
}

# Function to install dependencies
install_dependencies() {
  echo -e "${BLUE}Installing/Updating Python dependencies...${NC}"
  pip install --upgrade pip setuptools wheel > /dev/null
  pip install -r "$BACKEND_DIR/requirements.txt"
  
  echo -e "${BLUE}Installing/Updating Node.js dependencies in $FRONTEND_DIR...${NC}"
  if [ -d "$FRONTEND_DIR" ]; then
    (cd "$FRONTEND_DIR" && npm install)
  else
    echo -e "${RED}Error: Frontend directory $FRONTEND_DIR not found.${NC}"
    exit 1
  fi
}

# --- Main Execution ---

echo -e "${BLUE}Starting Nexora project setup...${NC}"

# 1. Check for required tools
if ! command_exists python3; then
  echo -e "${RED}Error: python3 is required but not installed.${NC}"
  exit 1
fi
if ! command_exists npm; then
  echo -e "${RED}Error: npm is required but not installed.${NC}"
  exit 1
fi

# 2. Setup Environment and Dependencies
ensure_venv
install_dependencies

# 3. Copy environment file if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  if [ -f "$PROJECT_ROOT/env.example" ]; then
    echo -e "${BLUE}Creating .env from env.example...${NC}"
    cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}Please review and update the .env file with your configuration.${NC}"
  else
    echo -e "${RED}Warning: env.example not found. Cannot create .env file.${NC}"
  fi
fi

# 4. Finalize
deactivate
echo -e "${GREEN}Nexora project setup completed successfully!${NC}"
echo -e "${GREEN}You can now run the application using: ./scripts/run_nexora.sh${NC}"
