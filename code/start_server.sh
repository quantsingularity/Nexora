#!/bin/bash

# Nexora Backend Startup Script

echo "================================================"
echo "Starting Nexora Backend Services"
echo "================================================"
echo ""

# Set default environment variables
export PORT=${PORT:-8000}
export HOST=${HOST:-0.0.0.0}
export FHIR_SERVER_URL=${FHIR_SERVER_URL:-http://mock-fhir-server/R4}
export AUDIT_DB_PATH=${AUDIT_DB_PATH:-audit/phi_access.db}

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p audit
mkdir -p data/synthetic
mkdir -p data/processed
mkdir -p models

echo "Environment Configuration:"
echo "  PORT: $PORT"
echo "  HOST: $HOST"
echo "  FHIR_SERVER_URL: $FHIR_SERVER_URL"
echo "  AUDIT_DB_PATH: $AUDIT_DB_PATH"
echo ""

# Check if we're in the code directory
if [ ! -f "run_rest_api.py" ]; then
    echo "Error: Must run this script from the 'code' directory"
    echo "Usage: cd code && ./start_server.sh"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check critical dependencies
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: Critical dependencies missing. Please install them first:"
    echo "  pip install fastapi uvicorn pydantic requests"
    exit 1
fi

echo "Dependencies OK"
echo ""

echo "Starting REST API server..."
echo "Server will be available at: http://${HOST}:${PORT}"
echo "API Documentation: http://localhost:${PORT}/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 run_rest_api.py
