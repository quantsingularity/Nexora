#!/bin/bash

# Nexora Project Setup Script (Comprehensive)

# Exit immediately if a command exits with a non-zero status.
set -e

# Prerequisites (ensure these are installed and configured):
# - Kubernetes cluster (e.g., minikube, k3s, or a cloud provider's Kubernetes service)
# - FHIR-compliant database (specific setup will depend on the chosen database)
# - NVIDIA GPU with CUDA 11.7+ (for model training and serving with GPU acceleration)
# - Python 3.10+ (the script will use python3.11 available in the environment)
# - Node.js & npm (for frontend components)
# - Docker 20.10+ (implicitly, due to Kubernetes and Helm usage)
# - make
# - dvc (Data Version Control)
# - helm (for Kubernetes deployments)
# - Expo CLI (for mobile-frontend, if running locally: `npm install -g expo-cli` or `yarn global add expo-cli`)

echo "Starting Nexora project setup..."

PROJECT_DIR="/projects_extracted/Nexora"

if [ ! -d "${PROJECT_DIR}" ]; then
  echo "Error: Project directory ${PROJECT_DIR} not found."
  echo "Please ensure the project is extracted correctly."
  exit 1
fi

cd "${PROJECT_DIR}"
echo "Changed directory to $(pwd)"

# 1. Initialize environment and pull DVC data (as per README.md)
# The README specifies 'make setup && dvc pull'

echo "Checking for Makefile..."
if [ ! -f "Makefile" ]; then
    echo "Error: Makefile not found in ${PROJECT_DIR}. Cannot run 'make setup'."
    # exit 1 # Commenting out exit to allow script to proceed if Makefile is missing but other parts can be set up.
else
    echo "Running 'make setup' to set up the initial environment..."
    make setup
fi

echo "Checking for DVC configuration (e.g., .dvc folder, dvc.yaml, dvc.lock)..."
if [ ! -d ".dvc" ] && [ ! -f "dvc.yaml" ] && [ ! -f "dvc.lock" ]; then
    echo "Warning: DVC configuration not found. Skipping 'dvc pull'. Ensure DVC is not required or manually configured."
else
    echo "Pulling data with DVC..."
    dvc pull
fi

# 2. Install Python dependencies
# The README mentions 'pip install -r requirements-clinical.txt'.
# We'll also check for a general requirements.txt or pyproject.toml for completeness.

echo "Setting up Python environment..."
# Create a virtual environment
if ! python3.11 -m venv venv_nexora_py; then
    echo "Failed to create Python virtual environment. Please check your Python installation."
else
    source venv_nexora_py/bin/activate
    echo "Python virtual environment 'venv_nexora_py' created and activated."

    # Check for standard requirements files first
    if [ -f "requirements.txt" ]; then
        echo "Found requirements.txt. Installing general Python dependencies..."
        pip3 install -r requirements.txt
        echo "General Python dependencies installed."
    elif [ -f "pyproject.toml" ]; then
        echo "Found pyproject.toml. Installing Python dependencies using pip (this might require build tools like poetry or flit if not a standard PEP 621 project)..."
        pip3 install .
        echo "Python dependencies from pyproject.toml installed."
    else
        echo "No general requirements.txt or pyproject.toml found at project root."
    fi

    # Install clinical dependencies as specified in README
    if [ -f "requirements-clinical.txt" ]; then
        echo "Found requirements-clinical.txt. Installing clinical Python dependencies..."
        pip3 install -r requirements-clinical.txt
        echo "Clinical Python dependencies installed."
    else
        echo "Warning: requirements-clinical.txt not found as mentioned in README. Clinical Python dependencies may need manual installation."
    fi

    echo "To activate the Python virtual environment later, run: source ${PROJECT_DIR}/venv_nexora_py/bin/activate"
    deactivate
    echo "Python virtual environment deactivated."
fi

# --- Web Frontend Setup (React/Parcel) ---
echo ""
echo "Setting up Nexora Web Frontend environment..."
WEB_FRONTEND_DIR="${PROJECT_DIR}/web-frontend"

if [ ! -d "${WEB_FRONTEND_DIR}" ]; then
    echo "Warning: Web Frontend directory ${WEB_FRONTEND_DIR} not found. Skipping Web Frontend setup."
else
    cd "${WEB_FRONTEND_DIR}"
    echo "Changed directory to $(pwd) for Web Frontend setup."

    if [ ! -f "package.json" ]; then
        echo "Warning: package.json not found in ${WEB_FRONTEND_DIR}. Skipping Node.js dependency installation for Web Frontend."
    else
        echo "Installing Web Frontend Node.js dependencies using npm..."
        if ! command -v npm &> /dev/null; then echo "npm command not found."; else npm install; fi
        echo "Web Frontend dependencies installed."
        echo "To start the Web Frontend (from ${WEB_FRONTEND_DIR}): npm start (or 'parcel src/index.html')"
        echo "To build the Web Frontend (from ${WEB_FRONTEND_DIR}): npm run build (or 'parcel build src/index.html')"
    fi
    cd "${PROJECT_DIR}" # Return to the main project directory
fi

# --- Mobile Frontend Setup (React Native/Expo) ---
echo ""
echo "Setting up Nexora Mobile Frontend environment..."
MOBILE_FRONTEND_DIR="${PROJECT_DIR}/mobile-frontend"

if [ ! -d "${MOBILE_FRONTEND_DIR}" ]; then
    echo "Warning: Mobile Frontend directory ${MOBILE_FRONTEND_DIR} not found. Skipping Mobile Frontend setup."
else
    cd "${MOBILE_FRONTEND_DIR}"
    echo "Changed directory to $(pwd) for Mobile Frontend setup."

    if [ ! -f "package.json" ]; then
        echo "Warning: package.json not found in ${MOBILE_FRONTEND_DIR}. Skipping Node.js dependency installation for Mobile Frontend."
    else
        echo "Installing Mobile Frontend Node.js dependencies using npm..."
        if ! command -v npm &> /dev/null; then echo "npm command not found."; else npm install; fi
        echo "Mobile Frontend dependencies installed."
        echo "To start the Mobile Frontend (from ${MOBILE_FRONTEND_DIR}): npm start (or 'expo start')"
        echo "Ensure Expo CLI is installed globally or use npx expo start."
    fi
    cd "${PROJECT_DIR}" # Return to the main project directory
fi

# 3. Reminders for other prerequisites and configurations (as per README.md)
echo ""
echo "Important Prerequisites & Configurations to ensure are manually set up:"
echo "  - Kubernetes cluster"
echo "  - FHIR-compliant database (connection details might be needed in config/clinical_config.yaml or environment variables)"
echo "  - NVIDIA GPU with CUDA 11.7+ (if GPU acceleration is needed)"
echo "  - Docker 20.10+ (ensure Docker daemon is running)"
echo "  - Helm (for Kubernetes deployment)"
echo "  - Review and update configuration files as needed, particularly 'config/clinical_config.yaml'."

echo ""
echo "Nexora project setup script finished."
echo "Please review any warnings and ensure all prerequisites are met."
echo "Refer to the project's readme.md for further instructions on data pipelines (e.g., 'make clinical-pipeline'), model training (e.g., 'make federated-train'), and deployment (e.g., 'helm install ...')."
