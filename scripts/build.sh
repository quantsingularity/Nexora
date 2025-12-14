#!/bin/bash

# Build script for Nexora project
# This script builds the frontend for production and prepares the code environment.

set -euo pipefail

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
code_DIR="$PROJECT_ROOT/src"
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

# Function to ensure Python virtual environment is set up and activated
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
  pip install -r "$code_DIR/requirements.txt" > /dev/null
  
  echo -e "${BLUE}Installing/Updating Node.js dependencies in $FRONTEND_DIR...${NC}"
  if [ -d "$FRONTEND_DIR" ]; then
    (cd "$FRONTEND_DIR" && npm install > /dev/null)
  else
    echo -e "${RED}Error: Frontend directory $FRONTEND_DIR not found.${NC}"
    exit 1
  fi
}

# --- Main Execution ---

echo -e "${BLUE}Starting Nexora build process...${NC}"

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

# 3. Build Frontend
echo -e "${BLUE}Building frontend for production...${NC}"
if [ -d "$FRONTEND_DIR" ]; then
  (cd "$FRONTEND_DIR" && npm run build)
  echo -e "${GREEN}Frontend build completed successfully.${NC}"
else
  echo -e "${RED}Error: Frontend directory $FRONTEND_DIR not found. Skipping frontend build.${NC}"
fi

# 4. Finalize code Environment
echo -e "${BLUE}Finalizing code environment...${NC}"
# No specific build step for the code in this simple structure,
# but this is where compilation, static file collection, etc., would go.
echo -e "${GREEN}code environment ready.${NC}"

# Deactivate virtual environment
deactivate

echo -e "${GREEN}Nexora build process completed!${NC}"
