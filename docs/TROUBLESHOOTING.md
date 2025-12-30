# Troubleshooting Guide

Common issues and solutions for Nexora platform.

## Table of Contents

- [Installation Issues](#installation-issues)
- [API Issues](#api-issues)
- [Model Issues](#model-issues)
- [FHIR Integration Issues](#fhir-integration-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)

---

## Installation Issues

### Issue: `pip install` fails with "No module named 'distutils'"

**Symptoms**:

```
ModuleNotFoundError: No module named 'distutils.cmd'
```

**Solution**:

```bash
# Ubuntu/Debian
sudo apt-get install python3.9-distutils python3.9-dev

# Or upgrade pip
python -m pip install --upgrade pip setuptools
```

---

### Issue: TensorFlow installation fails

**Symptoms**:

```
ERROR: Could not find a version that satisfies the requirement tensorflow==2.15.0
```

**Solution**:

Python 3.12 is not supported by TensorFlow 2.15. Use Python 3.9-3.11:

```bash
# Check Python version
python --version

# If 3.12, install compatible version
pip install tensorflow==2.16.0  # or use Python 3.11
```

---

### Issue: CUDA/GPU not detected

**Symptoms**:

```python
import torch
print(torch.cuda.is_available())  # Returns False
```

**Solution**:

```bash
# 1. Verify NVIDIA driver
nvidia-smi

# 2. Install CUDA toolkit 11.8+
# Download from https://developer.nvidia.com/cuda-downloads

# 3. Install correct PyTorch version
pip install torch==2.1.0+cu118 -f https://download.pytorch.org/whl/torch_stable.html

# 4. Verify
python -c "import torch; print(torch.cuda.is_available())"
```

---

### Issue: Port 8000 already in use

**Symptoms**:

```
ERROR: [Errno 48] Address already in use
```

**Solution**:

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
PORT=8080 python code/run_rest_api.py
```

---

### Issue: Permission denied creating audit directory

**Symptoms**:

```
PermissionError: [Errno 13] Permission denied: 'audit'
```

**Solution**:

```bash
# Create directory with proper permissions
sudo mkdir -p audit
sudo chown $USER:$USER audit

# Or change AUDIT_DB_PATH
export AUDIT_DB_PATH="$HOME/nexora/audit/phi_access.db"
```

---

## API Issues

### Issue: 404 Not Found on API endpoints

**Symptoms**:

```json
{ "detail": "Not Found" }
```

**Checklist**:

1. Verify API is running: `curl http://localhost:8000/health`
2. Check correct port: Default is 8000
3. Verify endpoint path: `/predict` not `/prediction`
4. Check API docs: `http://localhost:8000/docs`

---

### Issue: 422 Unprocessable Entity

**Symptoms**:

```json
{
  "detail": [
    {
      "loc": ["body", "patient_data", "demographics"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solution**:

Ensure request includes all required fields:

```python
# Correct request format
{
    "model_name": "readmission_v1",
    "patient_data": {
        "patient_id": "12345",  # Required
        "demographics": {...},   # Required
        "clinical_events": [...] # Required
    }
}
```

Check API docs for complete schema: `http://localhost:8000/docs`

---

### Issue: 500 Internal Server Error

**Symptoms**:

```json
{ "detail": "Internal server error" }
```

**Debug Steps**:

1. **Check logs**:

```bash
# View API logs
tail -f logs/api.log

# Or run with debug logging
LOG_LEVEL=DEBUG python code/run_rest_api.py
```

2. **Common causes**:

- Model not found in registry
- Invalid model configuration
- Database connection error
- Missing environment variables

3. **Verify configuration**:

```bash
# Check environment variables
env | grep NEXORA

# Validate configuration
python -c "from code.utils.config import load_config; load_config('config/clinical_config.yaml')"
```

---

## Model Issues

### Issue: Model not found

**Symptoms**:

```
ModelNotFoundError: Model 'readmission_v1' not found in registry
```

**Solution**:

```bash
# 1. Check model registry location
ls -la models/registry/

# 2. Verify MODEL_REGISTRY_PATH
echo $MODEL_REGISTRY_PATH

# 3. List available models
python -c "
from code.model_factory.model_registry import ModelRegistry
registry = ModelRegistry()
print(registry.list_models())
"

# 4. If empty, train or download model
# (Follow model training guide)
```

---

### Issue: Low prediction accuracy

**Symptoms**:

- AUROC < 0.70
- High false positive rate
- Poor calibration

**Debug Steps**:

1. **Check data quality**:

```python
from code.data_pipeline.clinical_etl import ClinicalETL

etl = ClinicalETL(config_path='config/clinical_config.yaml')
etl.validate_data(data)  # Check for issues
```

2. **Verify feature engineering**:

```python
# Check for missing features
features = etl.extract_features(data)
print(f"Missing values: {features.isnull().sum()}")
```

3. **Evaluate on validation set**:

```python
from code.monitoring.clinical_metrics import ClinicalMetricsCalculator

metrics = ClinicalMetricsCalculator()
results = metrics.calculate_all(predictions, ground_truth)
print(results)
```

4. **Check for data drift**:

```python
from code.monitoring.concept_drift import DriftDetector

detector = DriftDetector()
drift_detected = detector.detect(reference_data, current_data)
if drift_detected:
    print("Warning: Data drift detected. Model may need retraining.")
```

---

### Issue: Out of memory during prediction

**Symptoms**:

```
RuntimeError: CUDA out of memory
MemoryError: Unable to allocate array
```

**Solutions**:

1. **Reduce batch size**:

```python
# In batch_scoring.py
python scripts/batch_scoring.py --batch-size 32  # Reduce from 100
```

2. **Use CPU instead of GPU**:

```bash
export ENABLE_GPU=false
python code/run_rest_api.py
```

3. **Increase available memory**:

```bash
# Docker
docker run -m 16g nexora-api

# Kubernetes
resources:
  limits:
    memory: "16Gi"
```

---

## FHIR Integration Issues

### Issue: FHIR server connection timeout

**Symptoms**:

```
requests.exceptions.ConnectTimeout: HTTPSConnectionPool: Max retries exceeded
```

**Solutions**:

1. **Verify FHIR server URL**:

```bash
# Test connectivity
curl https://fhir-server.example.org/R4/metadata

# Set correct URL
export FHIR_SERVER_URL="https://fhir-server.example.org/R4"
```

2. **Check authentication**:

```bash
# If using OAuth2
export FHIR_TOKEN="your-valid-token"

# Test with token
curl -H "Authorization: Bearer $FHIR_TOKEN" \
  https://fhir-server.example.org/R4/Patient/123
```

3. **Increase timeout**:

```yaml
# config/clinical_config.yaml
data:
  fhir:
    timeout_seconds: 60 # Increase from 30
    retry_attempts: 5
```

---

### Issue: FHIR resource parsing error

**Symptoms**:

```
ValidationError: Invalid FHIR resource
```

**Solution**:

```python
# Verify FHIR resource format
from fhir.resources.patient import Patient

try:
    patient = Patient.parse_obj(fhir_data)
    print("Valid FHIR resource")
except Exception as e:
    print(f"Invalid resource: {e}")
    # Check FHIR version (should be R4)
```

---

## Database Issues

### Issue: Audit database locked

**Symptoms**:

```
sqlite3.OperationalError: database is locked
```

**Solution**:

```bash
# 1. Check for other processes
lsof audit/phi_access.db

# 2. Kill blocking processes
kill -9 <PID>

# 3. Use PostgreSQL for production
export DATABASE_URL="postgresql://user:pass@localhost:5432/nexora"
```

---

### Issue: Database migration fails

**Symptoms**:

```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Solution**:

```bash
# Reset to head
alembic downgrade base
alembic upgrade head

# Or recreate database
rm audit/phi_access.db
python scripts/init_audit_db.py
```

---

## Performance Issues

### Issue: Slow API response times

**Symptoms**:

- Response time > 2 seconds
- High CPU usage
- Memory leaks

**Debug Steps**:

1. **Profile code**:

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

2. **Check model caching**:

```bash
# Increase model cache size
export MODEL_CACHE_SIZE=5
```

3. **Use gRPC for better performance**:

```python
# Switch to gRPC client
from code.serving.grpc_client import GRPCClient
client = GRPCClient('localhost:50051')
```

4. **Enable response caching** (for identical requests):

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def predict_cached(patient_id, features):
    return model.predict(features)
```

---

### Issue: High memory usage

**Symptoms**:

- Memory usage grows over time
- OOM killer terminates process

**Solutions**:

1. **Check for memory leaks**:

```python
import tracemalloc

tracemalloc.start()
# Your code
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

2. **Clear model cache periodically**:

```python
from code.model_factory.model_registry import ModelRegistry

registry = ModelRegistry()
registry.clear_cache()
```

3. **Use garbage collection**:

```python
import gc
gc.collect()
```

---

## Deployment Issues

### Issue: Kubernetes pod crash loop

**Symptoms**:

```
kubectl get pods -n nexora
NAME                          READY   STATUS             RESTARTS
nexora-api-5f7b6d8c9-abcde    0/1     CrashLoopBackOff   5
```

**Debug Steps**:

1. **Check pod logs**:

```bash
kubectl logs -n nexora nexora-api-5f7b6d8c9-abcde
kubectl logs -n nexora nexora-api-5f7b6d8c9-abcde --previous
```

2. **Describe pod**:

```bash
kubectl describe pod -n nexora nexora-api-5f7b6d8c9-abcde
```

3. **Common causes**:

- Missing secrets/configmaps
- Invalid configuration
- Resource limits too low
- Health check failures

4. **Verify resources**:

```bash
kubectl get configmap -n nexora
kubectl get secret -n nexora
```

---

### Issue: Docker container won't start

**Symptoms**:

```
docker ps -a
CONTAINER ID   STATUS
abc123         Exited (1) 2 seconds ago
```

**Debug**:

```bash
# View container logs
docker logs abc123

# Run interactively for debugging
docker run -it --entrypoint /bin/bash nexora-api

# Check Docker build
docker build -t nexora-api . --no-cache
```

---

## Getting More Help

### Collecting Diagnostic Information

```bash
# Run environment health check
python scripts/environment_health_check.py --output health_status.json

# Generate system report
python -c "
import sys
import platform
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Architecture: {platform.machine()}')
"

# Check package versions
pip list | grep -E 'fastapi|tensorflow|torch|fhir'
```

### Reporting Issues

When reporting issues, include:

1. **Environment**:
   - OS and version
   - Python version
   - Installation method (pip/docker/k8s)

2. **Error details**:
   - Full error message
   - Stack trace
   - Logs

3. **Steps to reproduce**:
   - Minimal code example
   - Configuration files (remove secrets!)
   - Sample data (de-identified!)

4. **Expected vs actual behavior**

### Resources

- [GitHub Issues](https://github.com/abrar2030/Nexora/issues)
- [Documentation](README.md)
- [API Reference](API.md)
- [Configuration Guide](CONFIGURATION.md)

---
