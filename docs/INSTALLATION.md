# Installation Guide

Complete installation instructions for Nexora healthcare AI platform across different environments and operating systems.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Platform-Specific Installation](#platform-specific-installation)
- [Environment Setup](#environment-setup)
- [Verification](#verification)
- [Post-Installation](#post-installation)

---

## System Requirements

### Minimum Requirements

| Component            | Requirement                                             |
| -------------------- | ------------------------------------------------------- |
| **Operating System** | Linux (Ubuntu 20.04+), macOS 12+, Windows 10+ with WSL2 |
| **Python**           | 3.9 or higher                                           |
| **Memory**           | 8 GB RAM minimum, 16 GB recommended                     |
| **Storage**          | 10 GB free space                                        |
| **CPU**              | 4 cores minimum, 8 cores recommended                    |
| **GPU**              | Optional (CUDA 11.8+ for GPU acceleration)              |

### Recommended for Production

| Component   | Requirement                  |
| ----------- | ---------------------------- |
| **Memory**  | 32 GB RAM                    |
| **Storage** | 100 GB SSD                   |
| **CPU**     | 16+ cores                    |
| **GPU**     | NVIDIA GPU with 8+ GB VRAM   |
| **Network** | 1 Gbps+ for FHIR integration |

### Software Dependencies

- Python 3.9+
- pip 21.0+
- Git 2.30+
- Node.js 16+ (for web frontend)
- Docker 20.10+ (optional, for containerized deployment)
- Kubernetes 1.24+ (optional, for cluster deployment)

---

## Installation Methods

### Method 1: Pip Installation (Recommended for Development)

**Best for**: Development, testing, local experimentation

```bash
# Clone the repository
git clone https://github.com/abrar2030/Nexora.git
cd Nexora

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r code/requirements.txt

# Optional: Install development dependencies
pip install -r requirements-dev.txt  # If available
```

### Method 2: Docker Installation (Recommended for Production)

**Best for**: Production deployment, consistent environments, quick testing

```bash
# Clone the repository
git clone https://github.com/abrar2030/Nexora.git
cd Nexora

# Build Docker images
make docker-build

# Or build individual services
docker build -t nexora-api-gateway -f deployments/docker/api-gateway.Dockerfile .
docker build -t nexora-model-server -f deployments/docker/model-server.Dockerfile .
docker build -t nexora-fhir-connector -f deployments/docker/fhir-connector.Dockerfile .
```

### Method 3: Kubernetes Deployment

**Best for**: Enterprise production, high availability, scalable deployments

```bash
# Prerequisites: kubectl configured with cluster access

# Create namespace
kubectl create namespace nexora

# Deploy using Makefile
make deploy

# Or deploy manually
kubectl apply -f infrastructure/kubernetes/manifests/
```

---

## Platform-Specific Installation

### Ubuntu/Debian Linux

| Step                        | Command                                                         | Notes                |
| --------------------------- | --------------------------------------------------------------- | -------------------- |
| **1. Update system**        | `sudo apt-get update && sudo apt-get upgrade -y`                | Update package lists |
| **2. Install Python**       | `sudo apt-get install python3.9 python3.9-venv python3-pip -y`  | Python 3.9+ required |
| **3. Install Git**          | `sudo apt-get install git -y`                                   | Version control      |
| **4. Clone repository**     | `git clone https://github.com/abrar2030/Nexora.git`             | Get source code      |
| **5. Setup environment**    | `cd Nexora && python3 -m venv venv && source venv/bin/activate` | Isolated environment |
| **6. Install dependencies** | `pip install -r code/requirements.txt`                          | Python packages      |

### macOS

| Step                        | Command                                                                                           | Notes                |
| --------------------------- | ------------------------------------------------------------------------------------------------- | -------------------- |
| **1. Install Homebrew**     | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` | Package manager      |
| **2. Install Python**       | `brew install python@3.9`                                                                         | Python 3.9+          |
| **3. Install Git**          | `brew install git`                                                                                | Version control      |
| **4. Clone repository**     | `git clone https://github.com/abrar2030/Nexora.git`                                               | Get source code      |
| **5. Setup environment**    | `cd Nexora && python3 -m venv venv && source venv/bin/activate`                                   | Isolated environment |
| **6. Install dependencies** | `pip install -r code/requirements.txt`                                                            | Python packages      |

### Windows (with WSL2)

| Step                        | Command                                                         | Notes                      |
| --------------------------- | --------------------------------------------------------------- | -------------------------- |
| **1. Install WSL2**         | `wsl --install`                                                 | Run in PowerShell as Admin |
| **2. Install Ubuntu**       | `wsl --install -d Ubuntu-20.04`                                 | Linux distribution         |
| **3. Update system**        | `sudo apt-get update && sudo apt-get upgrade -y`                | Inside WSL                 |
| **4. Install Python**       | `sudo apt-get install python3.9 python3.9-venv python3-pip -y`  | Python 3.9+                |
| **5. Install Git**          | `sudo apt-get install git -y`                                   | Version control            |
| **6. Clone repository**     | `git clone https://github.com/abrar2030/Nexora.git`             | Get source code            |
| **7. Setup environment**    | `cd Nexora && python3 -m venv venv && source venv/bin/activate` | Isolated environment       |
| **8. Install dependencies** | `pip install -r code/requirements.txt`                          | Python packages            |

### Docker Desktop (All Platforms)

| Step                          | Command/Action                                      | Notes                                         |
| ----------------------------- | --------------------------------------------------- | --------------------------------------------- |
| **1. Install Docker Desktop** | Download from docker.com                            | Windows, macOS, Linux                         |
| **2. Start Docker**           | Launch Docker Desktop application                   | Ensure Docker daemon is running               |
| **3. Clone repository**       | `git clone https://github.com/abrar2030/Nexora.git` | Get source code                               |
| **4. Build images**           | `cd Nexora && make docker-build`                    | Build all services                            |
| **5. Run services**           | `docker-compose up -d`                              | Start all containers (if compose file exists) |

---

## Environment Setup

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
HOST=0.0.0.0
PORT=8000

# FHIR Server
FHIR_SERVER_URL=http://fhir-server:8080/R4

# Database (if applicable)
DATABASE_URL=postgresql://user:password@localhost:5432/nexora

# Audit Logging
AUDIT_DB_PATH=./audit/phi_access.db

# Model Configuration
MODEL_REGISTRY_PATH=./models/registry
DEFAULT_MODEL=readmission_v1

# Security
SECRET_KEY=your-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Compliance
ENABLE_AUDIT_LOGGING=true
PHI_DETECTION_ENABLED=true
```

### Configuration Files

1. **Copy example configurations**:

   ```bash
   cp config/clinical_config.example.yaml config/clinical_config.yaml
   ```

2. **Edit configuration** to match your environment:

   ```bash
   nano config/clinical_config.yaml
   ```

3. **Validate configuration**:
   ```bash
   python scripts/validate_config.py
   ```

---

## Verification

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.9+

# Check installed packages
pip list | grep -E "fastapi|tensorflow|torch|fhir"

# Run health check
python -c "from code.serving.rest_api import app; print('Import successful')"

# Start API server (in development mode)
python code/run_rest_api.py
```

### Test API Endpoints

Once the server is running:

```bash
# Health check
curl http://localhost:8000/health

# List available models
curl http://localhost:8000/models

# Interactive API docs
# Open browser: http://localhost:8000/docs
```

### Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
make test

# Or run with pytest directly
pytest tests/ -v

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/clinical_tests -v
```

---

## Post-Installation

### Setup Development Environment

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install development tools
pip install black flake8 mypy pytest-cov

# Run code formatting
make format

# Run linting
make lint
```

### Initialize Database (if applicable)

```bash
# Create audit database directory
mkdir -p audit

# Initialize database tables
python scripts/init_audit_db.py
```

### Load Sample Data

```bash
# Generate synthetic clinical data
python code/data/synthetic_clinical_data.py --output ./data/synthetic_patients.json --count 100

# Load data into system (if applicable)
python scripts/load_sample_data.py
```

### Start Frontend Services

**Web Frontend**:

```bash
cd web-frontend
npm install
npm start
# Access at http://localhost:3000
```

**Mobile Frontend**:

```bash
cd mobile-frontend
npm install
npm start
# Follow React Native setup instructions
```

**Clinical UI (Streamlit)**:

```bash
streamlit run code/interfaces/clinician_ui.py
# Access at http://localhost:8501
```

---

## Troubleshooting Installation

### Common Issues

**Issue**: `pip install` fails with "No module named 'distutils'"

- **Solution**: `sudo apt-get install python3.9-distutils`

**Issue**: TensorFlow installation fails

- **Solution**: Ensure Python 3.9-3.11 (TensorFlow 2.15 doesn't support 3.12+)
- Alternative: Use compatible version `pip install tensorflow==2.14.0`

**Issue**: CUDA/GPU not detected

- **Solution**: Install CUDA toolkit 11.8+ and cuDNN
- Verify: `python -c "import torch; print(torch.cuda.is_available())"`

**Issue**: Port 8000 already in use

- **Solution**: Change PORT in `.env` file or stop conflicting service
- Check: `lsof -i :8000` (Linux/macOS) or `netstat -ano | findstr :8000` (Windows)

**Issue**: Permission denied when creating audit directory

- **Solution**: `sudo mkdir -p audit && sudo chown $USER:$USER audit`

For more troubleshooting tips, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Next Steps

After successful installation:

1. Read the [Usage Guide](USAGE.md) for typical usage patterns
2. Explore [Examples](examples/) for hands-on tutorials
3. Review [Configuration](CONFIGURATION.md) to customize your setup
4. Check [API Reference](API.md) for integration details
5. Read [Contributing](CONTRIBUTING.md) if you want to contribute

---

## Getting Help

- **Installation issues**: Check [Troubleshooting](TROUBLESHOOTING.md)
- **Configuration help**: See [Configuration Guide](CONFIGURATION.md)
- **Bug reports**: [GitHub Issues](https://github.com/abrar2030/Nexora/issues)
- **Community support**: GitHub Discussions
