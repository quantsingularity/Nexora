#!/bin/bash

# Enhanced Run script for Nexora project
# This script starts both the backend and frontend components.
# It is designed to be run from the project root (Nexora/).

set -euo pipefail # Exit on error, exit on unset variable, fail on pipe error

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
BACKEND_DIR="$PROJECT_ROOT/src"
FRONTEND_DIR="$PROJECT_ROOT/web-frontend"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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
  pip install -r "$BACKEND_DIR/requirements.txt" > /dev/null
  
  echo -e "${BLUE}Installing/Updating Node.js dependencies in $FRONTEND_DIR...${NC}"
  if [ -d "$FRONTEND_DIR" ]; then
    (cd "$FRONTEND_DIR" && npm install > /dev/null)
  else
    echo -e "${RED}Error: Frontend directory $FRONTEND_DIR not found.${NC}"
    exit 1
  fi
}

# --- Main Execution ---

echo -e "${BLUE}Starting Nexora application...${NC}"

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

# 3. Start Backend Server
echo -e "${BLUE}Starting backend server...${NC}"
# Use gunicorn or similar for production, but for a simple run script, python is fine.
# Running from the project root to ensure correct path resolution
python "$BACKEND_DIR/app.py" &
BACKEND_PID=$!

# Wait for backend to initialize (simple sleep for demonstration)
echo -e "${BLUE}Waiting for backend to initialize...${NC}"
sleep 5

# 4. Start Frontend
echo -e "${BLUE}Starting frontend...${NC}"
(cd "$FRONTEND_DIR" && npm start) &
FRONTEND_PID=$!

# 5. Handle graceful shutdown
function cleanup {
  echo -e "\n${BLUE}Stopping services...${NC}"
  # Check if PIDs exist before killing
  if kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID"
  fi
  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID"
  fi
  echo -e "${GREEN}All services stopped${NC}"
  exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${GREEN}Nexora application is running!${NC}"
echo -e "${GREEN}Backend running with PID: ${BACKEND_PID}${NC}"
echo -e "${GREEN}Frontend running with PID: ${FRONTEND_PID}${NC}"
echo -e "${GREEN}Access the application at: http://localhost:3000${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Keep script running
wait
