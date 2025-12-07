#!/bin/bash

# Enhanced Linting and Fixing Script for Nexora Project
# This script is designed to be run from the project root (Nexora/).

set -euo pipefail # Exit on error, exit on unset variable, fail on pipe error

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
FRONTEND_DIR="$PROJECT_ROOT/web-frontend"
PYTHON_DIRS=("src" "tests" "notebooks")
JS_DIRS=("$FRONTEND_DIR/src")
YAML_DIRS=("config" "deployments" "infrastructure" ".github/workflows")
TERRAFORM_DIRS=("infrastructure/terraform" "deployments/terraform")

# --- Utility Functions ---

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to ensure Python virtual environment is set up and activated
ensure_venv() {
  echo "Ensuring Python virtual environment is set up..."
  if [ ! -d "$VENV_PATH" ]; then
    echo "Creating Python virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
  fi

  # Activate the virtual environment
  source "$VENV_PATH/bin/activate"
  echo "Virtual environment activated."

  # Install/Update Python dependencies
  echo "Installing/Updating Python dependencies from src/requirements.txt..."
  pip install --upgrade pip setuptools wheel > /dev/null
  pip install -r "$PROJECT_ROOT/src/requirements.txt"
  
  # Install linting tools
  echo "Installing/Updating Python linting tools..."
  pip install --upgrade black isort flake8 pylint nbqa pyyaml
}

# Function to ensure Node.js dependencies are installed
ensure_node_deps() {
  echo "Ensuring Node.js dependencies are installed in $FRONTEND_DIR..."
  if [ -d "$FRONTEND_DIR" ]; then
    (cd "$FRONTEND_DIR" && npm install)
  else
    echo "Warning: Frontend directory $FRONTEND_DIR not found. Skipping Node.js dependency check."
  fi
}

# --- Main Execution ---

echo "----------------------------------------"
echo "Starting linting and fixing process for Nexora..."
echo "----------------------------------------"

# 1. Environment Setup
ensure_venv
ensure_node_deps

# 2. Python Linting
echo "----------------------------------------"
echo "Running Python linting tools..."

# 2.1 Run Black (code formatter)
echo "Running Black code formatter..."
for dir in "${PYTHON_DIRS[@]}"; do
  if [ -d "$PROJECT_ROOT/$dir" ]; then
    echo "Formatting Python files in $dir..."
    python -m black "$PROJECT_ROOT/$dir"
  else
    echo "Directory $dir not found. Skipping Black formatting."
  fi
done

# 2.2 Run isort (import sorter)
echo "Running isort to sort imports..."
for dir in "${PYTHON_DIRS[@]}"; do
  if [ -d "$PROJECT_ROOT/$dir" ]; then
    echo "Sorting imports in Python files in $dir..."
    python -m isort "$PROJECT_ROOT/$dir"
  else
    echo "Directory $dir not found. Skipping isort."
  fi
done

# 2.3 Run flake8 (linter)
echo "Running flake8 linter..."
for dir in "${PYTHON_DIRS[@]}"; do
  if [ -d "$PROJECT_ROOT/$dir" ]; then
    echo "Linting Python files in $dir with flake8..."
    python -m flake8 "$PROJECT_ROOT/$dir"
  else
    echo "Directory $dir not found. Skipping flake8."
  fi
done

# 2.4 Run pylint (more comprehensive linter)
echo "Running pylint for more comprehensive linting..."
for dir in "${PYTHON_DIRS[@]}"; do
  if [ -d "$PROJECT_ROOT/$dir" ]; then
    echo "Linting Python files in $dir with pylint..."
    find "$PROJECT_ROOT/$dir" -type f -name "*.py" | xargs python -m pylint --disable=C0111,C0103,C0303,W0621,C0301,W0612,W0611,R0913,R0914,R0915
  else
    echo "Directory $dir not found. Skipping pylint."
  fi
done

# 2.5 Run linting on Jupyter notebooks
if [ -d "$PROJECT_ROOT/notebooks" ]; then
  echo "Running linting on Jupyter notebooks..."
  python -m nbqa black "$PROJECT_ROOT/notebooks"
  python -m nbqa isort "$PROJECT_ROOT/notebooks"
  python -m nbqa flake8 "$PROJECT_ROOT/notebooks"
else
  echo "Directory notebooks not found. Skipping notebook linting."
fi

# 3. JavaScript/TypeScript Linting (Assumes tools are installed locally in web-frontend)
echo "----------------------------------------"
echo "Running JavaScript/TypeScript linting tools..."

if [ -d "$FRONTEND_DIR" ]; then
  (
    cd "$FRONTEND_DIR"
    echo "Running ESLint for JavaScript/TypeScript files..."
    npx eslint "src" --ext .js,.jsx,.ts,.tsx --fix
    echo "Running Prettier for JavaScript/TypeScript files..."
    npx prettier --write "src/**/*.{js,jsx,ts,tsx}"
  )
else
  echo "Skipping JavaScript/TypeScript linting (frontend directory not found)."
fi

# 4. YAML Linting
echo "----------------------------------------"
echo "Running YAML linting tools..."

if command_exists yamllint; then
  echo "Running yamllint for YAML files..."
  for dir in "${YAML_DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
      echo "Linting YAML files in $dir with yamllint..."
      yamllint "$PROJECT_ROOT/$dir"
    else
      echo "Directory $dir not found. Skipping yamllint."
    fi
  done
else
  echo "yamllint not installed. Performing basic YAML validation using Python..."
  for dir in "${YAML_DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
      echo "Validating YAML files in $dir..."
      find "$PROJECT_ROOT/$dir" -type f \( -name "*.yaml" -o -name "*.yml" \) -exec python -c "import yaml; yaml.safe_load(open('{}', 'r'))" \;
    else
      echo "Directory $dir not found. Skipping YAML validation."
    fi
  done
fi

# 5. Terraform Linting
echo "----------------------------------------"
echo "Running Terraform linting tools..."

if command_exists terraform; then
  echo "Running terraform fmt and validate for Terraform files..."
  for dir in "${TERRAFORM_DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
      echo "Processing Terraform files in $dir..."
      (cd "$PROJECT_ROOT/$dir" && terraform fmt -recursive && terraform init -backend=false && terraform validate)
    else
      echo "Directory $dir not found. Skipping Terraform processing."
    fi
  done
else
  echo "Skipping Terraform linting (terraform not installed)."
fi

# 6. Common Fixes for All File Types
echo "----------------------------------------"
echo "Applying common fixes to all file types..."

# Fix trailing whitespace and ensure newline at end of file
find "$PROJECT_ROOT" -type f \( -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.yaml" -o -name "*.yml" -o -name "*.tf" -o -name "*.tfvars" \) \
  -not -path "*/node_modules/*" -not -path "*/venv/*" -not -path "*/dist/*" \
  -exec sed -i 's/[ \t]*$//' {} \; \
  -exec sh -c '[ -n "$(tail -c1 "$1")" ] && echo "" >> "$1"' sh {} \;

echo "Common fixes completed."

# Deactivate virtual environment
deactivate

echo "----------------------------------------"
echo "Linting and fixing process for Nexora completed!"
echo "----------------------------------------"
