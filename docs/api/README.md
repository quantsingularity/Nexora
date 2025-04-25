# API Documentation

This document provides comprehensive documentation for the Hospital Readmission Risk Prediction System APIs. The system exposes two main API interfaces: a REST API and a gRPC API.

## REST API

The REST API provides HTTP endpoints for model inference, data retrieval, and system management.

### Base URL

```
https://<deployment-url>/api/v1
```

### Authentication

All API requests require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

### Endpoints

#### Prediction Endpoints

##### GET /predict/readmission/{patient_id}

Get readmission risk prediction for a specific patient.

**Parameters:**
- `patient_id` (path): The unique identifier for the patient

**Response:**
```json
{
  "patient_id": "12345",
  "prediction": {
    "readmission_risk": 0.72,
    "confidence_interval": [0.65, 0.79],
    "risk_factors": [
      {"factor": "previous_admissions", "importance": 0.35},
      {"factor": "comorbidities", "importance": 0.28},
      {"factor": "medication_adherence", "importance": 0.21}
    ],
    "recommended_interventions": [
      {"intervention": "medication_review", "impact": "high"},
      {"intervention": "follow_up_appointment", "impact": "medium"}
    ]
  },
  "model_version": "2.3.0",
  "timestamp": "2025-04-25T10:30:45Z"
}
```

**Status Codes:**
- 200: Successful prediction
- 400: Invalid request
- 401: Unauthorized
- 404: Patient not found
- 500: Server error

##### POST /predict/batch

Submit a batch prediction request for multiple patients.

**Request Body:**
```json
{
  "patient_ids": ["12345", "67890", "54321"],
  "include_factors": true,
  "include_interventions": true
}
```

**Response:**
```json
{
  "predictions": [
    {
      "patient_id": "12345",
      "readmission_risk": 0.72,
      "risk_factors": [...],
      "recommended_interventions": [...]
    },
    {
      "patient_id": "67890",
      "readmission_risk": 0.35,
      "risk_factors": [...],
      "recommended_interventions": [...]
    },
    {
      "patient_id": "54321",
      "readmission_risk": 0.89,
      "risk_factors": [...],
      "recommended_interventions": [...]
    }
  ],
  "model_version": "2.3.0",
  "timestamp": "2025-04-25T10:32:15Z"
}
```

#### Data Endpoints

##### GET /patients/{patient_id}

Retrieve patient information.

**Parameters:**
- `patient_id` (path): The unique identifier for the patient

**Response:**
```json
{
  "patient_id": "12345",
  "demographics": {
    "age": 65,
    "gender": "female",
    "race": "caucasian"
  },
  "clinical_summary": {
    "diagnoses": ["I25.10", "E11.9", "I10"],
    "procedures": ["0210093", "5A1955Z"],
    "medications": ["metformin", "lisinopril", "atorvastatin"]
  },
  "admission_history": [
    {
      "admission_date": "2024-10-15",
      "discharge_date": "2024-10-22",
      "primary_diagnosis": "I25.10",
      "length_of_stay": 7
    },
    {
      "admission_date": "2023-05-03",
      "discharge_date": "2023-05-10",
      "primary_diagnosis": "J18.9",
      "length_of_stay": 7
    }
  ]
}
```

##### GET /metrics/model-performance

Retrieve model performance metrics.

**Query Parameters:**
- `start_date` (optional): Start date for metrics period (YYYY-MM-DD)
- `end_date` (optional): End date for metrics period (YYYY-MM-DD)
- `model_version` (optional): Specific model version to query

**Response:**
```json
{
  "overall": {
    "auc_roc": 0.82,
    "sensitivity": 0.75,
    "specificity": 0.84,
    "ppv": 0.68,
    "npv": 0.88,
    "calibration_slope": 1.02
  },
  "subgroups": {
    "age_65_plus": {
      "auc_roc": 0.79,
      "sensitivity": 0.72,
      "specificity": 0.88
    },
    "icu_patients": {
      "auc_roc": 0.85,
      "sensitivity": 0.81,
      "specificity": 0.79
    }
  },
  "fairness": {
    "equal_opportunity_diff": 0.03,
    "demographic_parity_ratio": 0.92
  },
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-03-31"
  },
  "model_version": "2.3.0"
}
```

#### Admin Endpoints

##### GET /admin/model-versions

List available model versions.

**Response:**
```json
{
  "models": [
    {
      "version": "2.3.0",
      "deployed_date": "2025-03-15T08:00:00Z",
      "status": "active",
      "performance": {
        "auc_roc": 0.82,
        "calibration_slope": 1.02
      }
    },
    {
      "version": "2.2.1",
      "deployed_date": "2025-01-10T09:30:00Z",
      "status": "archived",
      "performance": {
        "auc_roc": 0.79,
        "calibration_slope": 0.98
      }
    }
  ]
}
```

##### POST /admin/deploy-model

Deploy a new model version.

**Request Body:**
```json
{
  "model_version": "2.4.0",
  "model_registry_path": "models/readmission/2.4.0",
  "deployment_environment": "production"
}
```

**Response:**
```json
{
  "deployment_id": "dep-2025-04-25-001",
  "status": "in_progress",
  "estimated_completion": "2025-04-25T12:00:00Z"
}
```

## gRPC API

The gRPC API provides high-performance, low-latency access to the prediction service, suitable for integration with other systems.

### Service Definition

The gRPC service is defined in the following protobuf file:

```protobuf
syntax = "proto3";

package readmission;

service ReadmissionPrediction {
  // Get readmission risk prediction for a patient
  rpc PredictReadmissionRisk(PatientRequest) returns (PredictionResponse);
  
  // Batch prediction for multiple patients
  rpc BatchPredictReadmissionRisk(BatchPatientRequest) returns (BatchPredictionResponse);
  
  // Stream predictions for a list of patients
  rpc StreamPredictions(BatchPatientRequest) returns (stream PredictionResponse);
  
  // Bidirectional streaming for real-time predictions
  rpc RealTimePredictions(stream PatientRequest) returns (stream PredictionResponse);
}

message PatientRequest {
  string patient_id = 1;
  bool include_risk_factors = 2;
  bool include_interventions = 3;
}

message RiskFactor {
  string factor = 1;
  float importance = 2;
}

message Intervention {
  string intervention = 1;
  string impact = 2;
}

message PredictionResponse {
  string patient_id = 1;
  float readmission_risk = 2;
  repeated float confidence_interval = 3;
  repeated RiskFactor risk_factors = 4;
  repeated Intervention recommended_interventions = 5;
  string model_version = 6;
  string timestamp = 7;
}

message BatchPatientRequest {
  repeated string patient_ids = 1;
  bool include_risk_factors = 2;
  bool include_interventions = 3;
}

message BatchPredictionResponse {
  repeated PredictionResponse predictions = 1;
  string model_version = 2;
  string timestamp = 3;
}
```

### Client Example (Python)

```python
import grpc
from readmission_pb2 import PatientRequest, BatchPatientRequest
from readmission_pb2_grpc import ReadmissionPredictionStub

def get_prediction(patient_id):
    # Create a gRPC channel
    channel = grpc.secure_channel('grpc.readmission-prediction.org:443', 
                                  grpc.ssl_channel_credentials())
    
    # Create a stub (client)
    stub = ReadmissionPredictionStub(channel)
    
    # Create a request
    request = PatientRequest(
        patient_id=patient_id,
        include_risk_factors=True,
        include_interventions=True
    )
    
    # Make the call
    response = stub.PredictReadmissionRisk(request)
    
    print(f"Readmission risk: {response.readmission_risk}")
    print(f"Confidence interval: {response.confidence_interval}")
    
    print("Risk factors:")
    for factor in response.risk_factors:
        print(f"  - {factor.factor}: {factor.importance}")
    
    print("Recommended interventions:")
    for intervention in response.recommended_interventions:
        print(f"  - {intervention.intervention} (Impact: {intervention.impact})")
    
    return response

def batch_prediction(patient_ids):
    # Create a gRPC channel
    channel = grpc.secure_channel('grpc.readmission-prediction.org:443', 
                                  grpc.ssl_channel_credentials())
    
    # Create a stub (client)
    stub = ReadmissionPredictionStub(channel)
    
    # Create a batch request
    request = BatchPatientRequest(
        patient_ids=patient_ids,
        include_risk_factors=True,
        include_interventions=True
    )
    
    # Make the call
    response = stub.BatchPredictReadmissionRisk(request)
    
    for prediction in response.predictions:
        print(f"Patient {prediction.patient_id}: {prediction.readmission_risk}")
    
    return response
```

### Authentication

gRPC authentication uses JWT tokens with the following interceptor:

```python
import grpc

class AuthInterceptor(grpc.UnaryUnaryClientInterceptor, 
                      grpc.UnaryStreamClientInterceptor,
                      grpc.StreamUnaryClientInterceptor,
                      grpc.StreamStreamClientInterceptor):
    def __init__(self, token):
        self.token = token

    def _add_token(self, metadata):
        metadata = metadata or ()
        return tuple(metadata) + (('authorization', f'Bearer {self.token}'),)

    def intercept_unary_unary(self, continuation, client_call_details, request):
        metadata = self._add_token(client_call_details.metadata)
        new_details = client_call_details._replace(metadata=metadata)
        return continuation(new_details, request)

    # Similar implementations for other interceptor methods...

# Usage
token = "your_jwt_token"
interceptor = AuthInterceptor(token)
channel = grpc.secure_channel('grpc.readmission-prediction.org:443', 
                              grpc.ssl_channel_credentials())
channel = grpc.intercept_channel(channel, interceptor)
stub = ReadmissionPredictionStub(channel)
```

## Error Handling

Both REST and gRPC APIs use standard error codes:

| HTTP Status | gRPC Status | Description |
|-------------|-------------|-------------|
| 200 | OK | Successful operation |
| 400 | INVALID_ARGUMENT | Invalid request parameters |
| 401 | UNAUTHENTICATED | Authentication failure |
| 403 | PERMISSION_DENIED | Authorization failure |
| 404 | NOT_FOUND | Resource not found |
| 429 | RESOURCE_EXHAUSTED | Rate limit exceeded |
| 500 | INTERNAL | Server error |
| 503 | UNAVAILABLE | Service unavailable |

## Rate Limiting

API requests are rate-limited based on client credentials:

- Standard tier: 10 requests/second
- Premium tier: 50 requests/second
- Enterprise tier: 200 requests/second

Rate limit headers are included in REST API responses:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1619395200
```

## Versioning

The API follows semantic versioning:

- Major version changes (v1 → v2) may include breaking changes
- Minor version changes (v1.1 → v1.2) add features in a backward-compatible manner
- Patch version changes (v1.1.0 → v1.1.1) include backward-compatible bug fixes

API versions are included in the URL path for REST APIs and in the package name for gRPC APIs.
