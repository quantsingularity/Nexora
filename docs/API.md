# API Reference

Complete reference for Nexora REST API endpoints, request/response schemas, and integration examples.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Overview

The Nexora API provides programmatic access to:

- **Readmission risk predictions** using ML models
- **FHIR-based patient data integration**
- **Model management** and version control
- **Audit logging** and compliance features

### API Characteristics

| Feature              | Details                                |
| -------------------- | -------------------------------------- |
| **Protocol**         | HTTP/HTTPS                             |
| **Format**           | JSON                                   |
| **Style**            | RESTful                                |
| **Documentation**    | OpenAPI 3.0 (Swagger)                  |
| **Interactive Docs** | `/docs` (Swagger UI), `/redoc` (ReDoc) |

---

## Authentication

### API Key Authentication (Recommended)

Include API key in request header:

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/models
```

### Bearer Token Authentication

For production deployments with OAuth2/JWT:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/predict
```

### Environment Variable

Set API key in environment:

```bash
export NEXORA_API_KEY="your-api-key"
```

---

## Base URL

| Environment     | Base URL                                 |
| --------------- | ---------------------------------------- |
| **Development** | `http://localhost:8000`                  |
| **Staging**     | `https://staging-api.nexora.example.com` |
| **Production**  | `https://api.nexora.example.com`         |

---

## Endpoints

### Health & Status

#### GET /health

Check API server health status.

**Parameters**: None

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example**:

```bash
curl http://localhost:8000/health
```

```python
import requests
response = requests.get("http://localhost:8000/health")
print(response.json())
```

---

### Model Management

#### GET /models

List all available prediction models.

**Parameters**: None

**Response**: `200 OK`

```json
{
  "models": [
    {
      "name": "readmission_v1",
      "version": "1.0.0",
      "type": "DeepFM",
      "status": "active",
      "description": "30-day readmission risk prediction",
      "performance": {
        "auroc": 0.82,
        "auprc": 0.76
      }
    },
    {
      "name": "readmission_transformer",
      "version": "2.0.0",
      "type": "Transformer",
      "status": "active",
      "description": "Transformer-based readmission prediction"
    }
  ]
}
```

**Example**:

```bash
curl http://localhost:8000/models
```

```python
import requests
response = requests.get("http://localhost:8000/models")
models = response.json()['models']
for model in models:
    print(f"{model['name']} v{model['version']} - AUROC: {model.get('performance', {}).get('auroc', 'N/A')}")
```

---

### Prediction

#### POST /predict

Generate readmission risk prediction for a patient.

**Request Body**: `PredictionRequest` (JSON)

| Field           | Type   | Required | Description                     | Example                |
| --------------- | ------ | -------: | ------------------------------- | ---------------------- |
| `model_name`    | string |       ✅ | Model identifier                | `"readmission_v1"`     |
| `model_version` | string |       ❌ | Model version (default: latest) | `"1.0.0"`              |
| `patient_data`  | object |       ✅ | Patient clinical data           | See PatientData schema |
| `request_id`    | string |       ❌ | Custom request ID               | `"req_12345"`          |

**PatientData Schema**:

| Field             | Type   | Required | Description               | Example                                     |
| ----------------- | ------ | -------: | ------------------------- | ------------------------------------------- |
| `patient_id`      | string |       ✅ | Unique patient identifier | `"12345"`                                   |
| `demographics`    | object |       ✅ | Age, gender, race, etc.   | `{"age": 65, "gender": "M"}`                |
| `clinical_events` | array  |       ✅ | Diagnoses, procedures     | `[{"type": "diagnosis", "code": "I50.9"}]`  |
| `lab_results`     | array  |       ❌ | Laboratory test results   | `[{"name": "HbA1c", "value": 8.2}]`         |
| `medications`     | array  |       ❌ | Current medications       | `[{"name": "Metformin", "dose": "1000mg"}]` |

**Response**: `200 OK`

```json
{
  "request_id": "req_20240115103000",
  "model_name": "readmission_v1",
  "model_version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "predictions": {
    "risk": 0.75,
    "risk_level": "high",
    "confidence_interval": [0.65, 0.85],
    "top_features": ["previous_admissions", "heart_failure", "age_65_plus"]
  },
  "explanations": {
    "method": "SHAP",
    "feature_contributions": {
      "previous_admissions": 0.25,
      "heart_failure": 0.2,
      "age_65_plus": 0.15,
      "diabetes": 0.1,
      "kidney_disease": 0.05
    }
  },
  "uncertainty": {
    "confidence_interval": [0.65, 0.85],
    "standard_error": 0.05
  }
}
```

**Example**:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "readmission_v1",
    "patient_data": {
      "patient_id": "12345",
      "demographics": {
        "age": 68,
        "gender": "M",
        "race": "Caucasian"
      },
      "clinical_events": [
        {
          "type": "diagnosis",
          "code": "I50.9",
          "description": "Heart failure, unspecified"
        },
        {
          "type": "diagnosis",
          "code": "E11.9",
          "description": "Type 2 diabetes mellitus"
        }
      ],
      "lab_results": [
        {"name": "HbA1c", "value": 8.2, "unit": "%"},
        {"name": "eGFR", "value": 45, "unit": "mL/min/1.73m²"}
      ],
      "medications": [
        {"name": "Metformin", "dose": "1000mg", "frequency": "BID"},
        {"name": "Lisinopril", "dose": "10mg", "frequency": "QD"}
      ]
    }
  }'
```

```python
import requests

payload = {
    "model_name": "readmission_v1",
    "patient_data": {
        "patient_id": "12345",
        "demographics": {"age": 68, "gender": "M"},
        "clinical_events": [
            {"type": "diagnosis", "code": "I50.9", "description": "Heart failure"}
        ],
        "lab_results": [
            {"name": "HbA1c", "value": 8.2, "unit": "%"}
        ]
    }
}

response = requests.post(
    "http://localhost:8000/predict",
    json=payload
)

result = response.json()
print(f"Risk: {result['predictions']['risk']:.2%}")
print(f"Level: {result['predictions']['risk_level']}")
print(f"Top Factors: {', '.join(result['predictions']['top_features'][:3])}")
```

---

### FHIR Integration

#### POST /fhir/patient/{patient_id}/predict

Generate prediction using patient data from FHIR server.

**Path Parameters**:

| Parameter    | Type   | Required | Description             | Example         |
| ------------ | ------ | -------: | ----------------------- | --------------- |
| `patient_id` | string |       ✅ | FHIR patient identifier | `"patient-123"` |

**Query Parameters**:

| Parameter       | Type   | Required | Description   | Example            |
| --------------- | ------ | -------: | ------------- | ------------------ |
| `model_name`    | string |       ✅ | Model to use  | `"readmission_v1"` |
| `model_version` | string |       ❌ | Model version | `"1.0.0"`          |

**Response**: Same as `/predict` endpoint

**Example**:

```bash
curl -X POST "http://localhost:8000/fhir/patient/patient-123/predict?model_name=readmission_v1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

```python
import requests

response = requests.post(
    "http://localhost:8000/fhir/patient/patient-123/predict",
    params={"model_name": "readmission_v1"},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

prediction = response.json()
print(f"Risk: {prediction['predictions']['risk']:.2%}")
```

**Configuration**:

Set FHIR server URL in environment:

```bash
export FHIR_SERVER_URL="https://fhir-server.example.org/R4"
```

---

## Data Models

### PredictionRequest

```json
{
  "model_name": "string",
  "model_version": "string | null",
  "patient_data": {
    "patient_id": "string",
    "demographics": {
      "age": "integer",
      "gender": "string",
      "race": "string | null",
      "ethnicity": "string | null"
    },
    "clinical_events": [
      {
        "type": "string",
        "code": "string",
        "description": "string | null",
        "timestamp": "string | null"
      }
    ],
    "lab_results": [
      {
        "name": "string",
        "value": "number",
        "unit": "string",
        "timestamp": "string | null"
      }
    ],
    "medications": [
      {
        "name": "string",
        "dose": "string",
        "frequency": "string",
        "route": "string | null"
      }
    ]
  },
  "request_id": "string | null"
}
```

### PredictionResponse

```json
{
  "request_id": "string",
  "model_name": "string",
  "model_version": "string",
  "timestamp": "string (ISO 8601)",
  "predictions": {
    "risk": "number (0.0 - 1.0)",
    "risk_level": "string (low | medium | high)",
    "confidence_interval": ["number", "number"],
    "top_features": ["string"]
  },
  "explanations": {
    "method": "string",
    "feature_contributions": {
      "feature_name": "number"
    }
  },
  "uncertainty": {
    "confidence_interval": ["number", "number"],
    "standard_error": "number"
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP Status Codes

| Code  | Status                | Description                       |
| ----- | --------------------- | --------------------------------- |
| `200` | OK                    | Request successful                |
| `400` | Bad Request           | Invalid request data              |
| `401` | Unauthorized          | Missing or invalid authentication |
| `403` | Forbidden             | Insufficient permissions          |
| `404` | Not Found             | Resource not found                |
| `422` | Unprocessable Entity  | Validation error                  |
| `429` | Too Many Requests     | Rate limit exceeded               |
| `500` | Internal Server Error | Server error                      |
| `503` | Service Unavailable   | Service temporarily unavailable   |

### Common Error Scenarios

#### Invalid Patient Data

**Request**:

```json
{
  "model_name": "readmission_v1",
  "patient_data": {
    "patient_id": "12345"
    // Missing required fields
  }
}
```

**Response**: `422 Unprocessable Entity`

```json
{
  "detail": "Validation error: demographics is required",
  "error_code": "VALIDATION_ERROR"
}
```

#### Model Not Found

**Response**: `404 Not Found`

```json
{
  "detail": "Model 'nonexistent_model' not found",
  "error_code": "MODEL_NOT_FOUND"
}
```

#### Rate Limit Exceeded

**Response**: `429 Too Many Requests`

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

---

## Rate Limiting

### Default Limits

| Plan            | Requests per minute | Requests per day |
| --------------- | ------------------: | ---------------: |
| **Development** |                  60 |           10,000 |
| **Standard**    |                 300 |           50,000 |
| **Enterprise**  |               1,000 |        Unlimited |

### Rate Limit Headers

Response includes rate limit information:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1705318200
```

### Handling Rate Limits

```python
import requests
import time

def make_request_with_retry(url, payload, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=payload)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue

        return response

    raise Exception("Max retries exceeded")
```

---

## Code Examples

### Python Client

```python
import requests
from typing import Dict, Any

class NexoraClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {}
        if api_key:
            self.headers['X-API-Key'] = api_key

    def predict(self, model_name: str, patient_data: Dict[str, Any]) -> Dict:
        """Make prediction for a patient."""
        response = requests.post(
            f"{self.base_url}/predict",
            json={
                "model_name": model_name,
                "patient_data": patient_data
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_models(self) -> list:
        """List available models."""
        response = requests.get(
            f"{self.base_url}/models",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['models']

# Usage
client = NexoraClient("http://localhost:8000", api_key="your-key")

patient = {
    "patient_id": "12345",
    "demographics": {"age": 65, "gender": "M"},
    "clinical_events": [
        {"type": "diagnosis", "code": "I50.9"}
    ]
}

result = client.predict("readmission_v1", patient)
print(f"Risk: {result['predictions']['risk']:.2%}")
```

### JavaScript/Node.js Client

```javascript
const axios = require("axios");

class NexoraClient {
  constructor(baseURL, apiKey) {
    this.client = axios.create({
      baseURL: baseURL,
      headers: apiKey ? { "X-API-Key": apiKey } : {},
    });
  }

  async predict(modelName, patientData) {
    const response = await this.client.post("/predict", {
      model_name: modelName,
      patient_data: patientData,
    });
    return response.data;
  }

  async listModels() {
    const response = await this.client.get("/models");
    return response.data.models;
  }
}

// Usage
const client = new NexoraClient("http://localhost:8000", "your-key");

const patient = {
  patient_id: "12345",
  demographics: { age: 65, gender: "M" },
  clinical_events: [{ type: "diagnosis", code: "I50.9" }],
};

client.predict("readmission_v1", patient).then((result) => {
  console.log(`Risk: ${(result.predictions.risk * 100).toFixed(1)}%`);
});
```

---

## Interactive API Documentation

### Swagger UI

Access interactive API documentation at:

```
http://localhost:8000/docs
```

Features:

- Try API endpoints directly in browser
- Automatic request/response validation
- Schema exploration
- Example values

### ReDoc

Alternative documentation interface:

```
http://localhost:8000/redoc
```

Features:

- Clean, readable documentation
- Responsive design
- Downloadable OpenAPI spec

---

## Next Steps

- Review [Usage Guide](USAGE.md) for integration patterns
- Explore [Examples](examples/) for complete workflows
- Check [Configuration](CONFIGURATION.md) for API settings
- Read [Troubleshooting](TROUBLESHOOTING.md) for common issues
