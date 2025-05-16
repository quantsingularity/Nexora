# Nexora Project Makefile
# Comprehensive build, test, and deployment system for the Nexora healthcare ML platform

# Variables
SHELL := /bin/bash
PYTHON := python3
PIP := pip3
PYTEST := pytest
DOCKER := docker
KUBECTL := kubectl
NAMESPACE := nexora
VERSION := $(shell cat VERSION)
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT := $(shell git rev-parse HEAD)
GIT_TAG := $(shell git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")

# Directories
SRC_DIR := src
SCRIPTS_DIR := scripts
CONFIG_DIR := config
TESTS_DIR := tests
NOTEBOOKS_DIR := notebooks
BUILD_DIR := build
DIST_DIR := dist
DOCS_DIR := docs
DEPLOY_DIR := deployments

# Python package settings
PACKAGE_NAME := nexora
VENV_DIR := venv
REQUIREMENTS := requirements.txt
DEV_REQUIREMENTS := requirements-dev.txt

# Docker settings
DOCKER_REGISTRY := nexora
DOCKER_IMAGE_PREFIX := nexora
MODEL_SERVER_IMAGE := $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_PREFIX)-model-server
FEATURE_SERVER_IMAGE := $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_PREFIX)-feature-server
API_GATEWAY_IMAGE := $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_PREFIX)-api-gateway
FHIR_CONNECTOR_IMAGE := $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_PREFIX)-fhir-connector

# Kubernetes settings
K8S_MANIFESTS := $(DEPLOY_DIR)/k8s
K8S_CONFIG := $(CONFIG_DIR)/k8s

# Default target
.PHONY: all
all: clean setup test build

# Setup development environment
.PHONY: setup
setup: venv install-dev

# Create virtual environment
.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	@test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created at $(VENV_DIR)"

# Install dependencies
.PHONY: install
install: venv
	@echo "Installing dependencies..."
	@. $(VENV_DIR)/bin/activate && $(PIP) install -U pip
	@. $(VENV_DIR)/bin/activate && $(PIP) install -r $(REQUIREMENTS)
	@echo "Dependencies installed."

# Install development dependencies
.PHONY: install-dev
install-dev: install
	@echo "Installing development dependencies..."
	@. $(VENV_DIR)/bin/activate && $(PIP) install -r $(DEV_REQUIREMENTS)
	@echo "Development dependencies installed."

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR) .pytest_cache .coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
	@echo "Clean complete."

# Run tests
.PHONY: test
test: test-unit test-integration test-clinical

# Run unit tests
.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	@. $(VENV_DIR)/bin/activate && $(PYTEST) $(TESTS_DIR)/unit -v

# Run integration tests
.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	@. $(VENV_DIR)/bin/activate && $(PYTEST) $(TESTS_DIR)/integration -v

# Run clinical tests
.PHONY: test-clinical
test-clinical:
	@echo "Running clinical tests..."
	@. $(VENV_DIR)/bin/activate && $(PYTEST) $(TESTS_DIR)/clinical_tests -v

# Run model tests
.PHONY: test-model
test-model:
	@echo "Running model tests..."
	@. $(VENV_DIR)/bin/activate && $(PYTEST) $(TESTS_DIR)/model_tests -v

# Run all tests with coverage
.PHONY: test-coverage
test-coverage:
	@echo "Running tests with coverage..."
	@. $(VENV_DIR)/bin/activate && $(PYTEST) --cov=$(SRC_DIR) --cov-report=html --cov-report=term $(TESTS_DIR)
	@echo "Coverage report generated in htmlcov/"

# Build Python package
.PHONY: build
build:
	@echo "Building Python package..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) setup.py sdist bdist_wheel
	@echo "Build complete. Artifacts in $(DIST_DIR)/"

# Build Docker images
.PHONY: docker-build
docker-build: docker-build-model-server docker-build-feature-server docker-build-api-gateway docker-build-fhir-connector

# Build model server Docker image
.PHONY: docker-build-model-server
docker-build-model-server:
	@echo "Building model server Docker image..."
	@$(DOCKER) build -t $(MODEL_SERVER_IMAGE):$(VERSION) \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		-f $(DEPLOY_DIR)/docker/model-server.Dockerfile .
	@$(DOCKER) tag $(MODEL_SERVER_IMAGE):$(VERSION) $(MODEL_SERVER_IMAGE):latest
	@echo "Model server Docker image built: $(MODEL_SERVER_IMAGE):$(VERSION)"

# Build feature server Docker image
.PHONY: docker-build-feature-server
docker-build-feature-server:
	@echo "Building feature server Docker image..."
	@$(DOCKER) build -t $(FEATURE_SERVER_IMAGE):$(VERSION) \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		-f $(DEPLOY_DIR)/docker/feature-server.Dockerfile .
	@$(DOCKER) tag $(FEATURE_SERVER_IMAGE):$(VERSION) $(FEATURE_SERVER_IMAGE):latest
	@echo "Feature server Docker image built: $(FEATURE_SERVER_IMAGE):$(VERSION)"

# Build API gateway Docker image
.PHONY: docker-build-api-gateway
docker-build-api-gateway:
	@echo "Building API gateway Docker image..."
	@$(DOCKER) build -t $(API_GATEWAY_IMAGE):$(VERSION) \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		-f $(DEPLOY_DIR)/docker/api-gateway.Dockerfile .
	@$(DOCKER) tag $(API_GATEWAY_IMAGE):$(VERSION) $(API_GATEWAY_IMAGE):latest
	@echo "API gateway Docker image built: $(API_GATEWAY_IMAGE):$(VERSION)"

# Build FHIR connector Docker image
.PHONY: docker-build-fhir-connector
docker-build-fhir-connector:
	@echo "Building FHIR connector Docker image..."
	@$(DOCKER) build -t $(FHIR_CONNECTOR_IMAGE):$(VERSION) \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		-f $(DEPLOY_DIR)/docker/fhir-connector.Dockerfile .
	@$(DOCKER) tag $(FHIR_CONNECTOR_IMAGE):$(VERSION) $(FHIR_CONNECTOR_IMAGE):latest
	@echo "FHIR connector Docker image built: $(FHIR_CONNECTOR_IMAGE):$(VERSION)"

# Push Docker images
.PHONY: docker-push
docker-push: docker-push-model-server docker-push-feature-server docker-push-api-gateway docker-push-fhir-connector

# Push model server Docker image
.PHONY: docker-push-model-server
docker-push-model-server:
	@echo "Pushing model server Docker image..."
	@$(DOCKER) push $(MODEL_SERVER_IMAGE):$(VERSION)
	@$(DOCKER) push $(MODEL_SERVER_IMAGE):latest
	@echo "Model server Docker image pushed: $(MODEL_SERVER_IMAGE):$(VERSION)"

# Push feature server Docker image
.PHONY: docker-push-feature-server
docker-push-feature-server:
	@echo "Pushing feature server Docker image..."
	@$(DOCKER) push $(FEATURE_SERVER_IMAGE):$(VERSION)
	@$(DOCKER) push $(FEATURE_SERVER_IMAGE):latest
	@echo "Feature server Docker image pushed: $(FEATURE_SERVER_IMAGE):$(VERSION)"

# Push API gateway Docker image
.PHONY: docker-push-api-gateway
docker-push-api-gateway:
	@echo "Pushing API gateway Docker image..."
	@$(DOCKER) push $(API_GATEWAY_IMAGE):$(VERSION)
	@$(DOCKER) push $(API_GATEWAY_IMAGE):latest
	@echo "API gateway Docker image pushed: $(API_GATEWAY_IMAGE):$(VERSION)"

# Push FHIR connector Docker image
.PHONY: docker-push-fhir-connector
docker-push-fhir-connector:
	@echo "Pushing FHIR connector Docker image..."
	@$(DOCKER) push $(FHIR_CONNECTOR_IMAGE):$(VERSION)
	@$(DOCKER) push $(FHIR_CONNECTOR_IMAGE):latest
	@echo "FHIR connector Docker image pushed: $(FHIR_CONNECTOR_IMAGE):$(VERSION)"

# Deploy to Kubernetes
.PHONY: deploy
deploy: deploy-namespace deploy-config deploy-services

# Create Kubernetes namespace
.PHONY: deploy-namespace
deploy-namespace:
	@echo "Creating Kubernetes namespace..."
	@$(KUBECTL) create namespace $(NAMESPACE) --dry-run=client -o yaml | $(KUBECTL) apply -f -
	@echo "Namespace $(NAMESPACE) created or already exists."

# Deploy Kubernetes configurations
.PHONY: deploy-config
deploy-config: deploy-namespace
	@echo "Deploying Kubernetes configurations..."
	@$(KUBECTL) apply -f $(K8S_CONFIG)/configmaps.yaml -n $(NAMESPACE)
	@$(KUBECTL) apply -f $(K8S_CONFIG)/secrets.yaml -n $(NAMESPACE)
	@echo "Kubernetes configurations deployed."

# Deploy Kubernetes services
.PHONY: deploy-services
deploy-services: deploy-namespace deploy-config
	@echo "Deploying Kubernetes services..."
	@$(KUBECTL) apply -f $(K8S_MANIFESTS)/feature_server.yaml -n $(NAMESPACE)
	@$(KUBECTL) apply -f $(K8S_MANIFESTS)/model_serving.yaml -n $(NAMESPACE)
	@$(KUBECTL) apply -f $(K8S_MANIFESTS)/api_gateway.yaml -n $(NAMESPACE)
	@$(KUBECTL) apply -f $(K8S_MANIFESTS)/fhir_connector.yaml -n $(NAMESPACE)
	@echo "Kubernetes services deployed."

# Generate documentation
.PHONY: docs
docs:
	@echo "Generating documentation..."
	@. $(VENV_DIR)/bin/activate && cd $(DOCS_DIR) && make html
	@echo "Documentation generated in $(DOCS_DIR)/build/html/"

# Run linting
.PHONY: lint
lint:
	@echo "Running linting..."
	@. $(VENV_DIR)/bin/activate && flake8 $(SRC_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)
	@echo "Linting complete."

# Format code
.PHONY: format
format:
	@echo "Formatting code..."
	@. $(VENV_DIR)/bin/activate && black $(SRC_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)
	@echo "Formatting complete."

# Run type checking
.PHONY: type-check
type-check:
	@echo "Running type checking..."
	@. $(VENV_DIR)/bin/activate && mypy $(SRC_DIR)
	@echo "Type checking complete."

# Run security checks
.PHONY: security-check
security-check:
	@echo "Running security checks..."
	@. $(VENV_DIR)/bin/activate && bandit -r $(SRC_DIR)
	@echo "Security checks complete."

# Run notebooks
.PHONY: notebooks
notebooks:
	@echo "Starting Jupyter notebook server..."
	@. $(VENV_DIR)/bin/activate && jupyter notebook --notebook-dir=$(NOTEBOOKS_DIR)

# Run batch scoring
.PHONY: batch-score
batch-score:
	@echo "Running batch scoring..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) $(SCRIPTS_DIR)/batch_scoring.py
	@echo "Batch scoring complete."

# Deploy FHIR server
.PHONY: deploy-fhir
deploy-fhir:
	@echo "Deploying FHIR server..."
	@bash $(SCRIPTS_DIR)/deploy_fhir.sh
	@echo "FHIR server deployment complete."

# Run data lineage
.PHONY: data-lineage
data-lineage:
	@echo "Running data lineage..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) $(SCRIPTS_DIR)/data_lineage.py
	@echo "Data lineage complete."

# Help target
.PHONY: help
help:
	@echo "Nexora Makefile Help"
	@echo "===================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "  all               : Clean, setup, test, and build"
	@echo "  setup             : Set up development environment"
	@echo "  venv              : Create virtual environment"
	@echo "  install           : Install dependencies"
	@echo "  install-dev       : Install development dependencies"
	@echo "  clean             : Clean build artifacts"
	@echo "  test              : Run all tests"
	@echo "  test-unit         : Run unit tests"
	@echo "  test-integration  : Run integration tests"
	@echo "  test-clinical     : Run clinical tests"
	@echo "  test-model        : Run model tests"
	@echo "  test-coverage     : Run tests with coverage"
	@echo "  build             : Build Python package"
	@echo "  docker-build      : Build all Docker images"
	@echo "  docker-push       : Push all Docker images"
	@echo "  deploy            : Deploy to Kubernetes"
	@echo "  docs              : Generate documentation"
	@echo "  lint              : Run linting"
	@echo "  format            : Format code"
	@echo "  type-check        : Run type checking"
	@echo "  security-check    : Run security checks"
	@echo "  notebooks         : Start Jupyter notebook server"
	@echo "  batch-score       : Run batch scoring"
	@echo "  deploy-fhir       : Deploy FHIR server"
	@echo "  data-lineage      : Run data lineage"
	@echo "  help              : Show this help message"
	@echo ""
	@echo "For more information, see the README.md file."
