# Example: Basic Prediction

This example demonstrates how to make a basic readmission risk prediction using the Nexora API.

## Prerequisites

- Nexora API server running (`python code/run_rest_api.py`)
- API accessible at `http://localhost:8000`

## Step 1: Prepare Patient Data

Create a JSON file with patient information:

```json
{
  "model_name": "readmission_v1",
  "patient_data": {
    "patient_id": "12345",
    "demographics": {
      "age": 68,
      "gender": "M",
      "race": "Caucasian",
      "ethnicity": "Non-Hispanic"
    },
    "clinical_events": [
      {
        "type": "diagnosis",
        "code": "I50.9",
        "description": "Heart failure, unspecified",
        "timestamp": "2024-01-10T08:30:00Z"
      },
      {
        "type": "diagnosis",
        "code": "E11.9",
        "description": "Type 2 diabetes mellitus without complications",
        "timestamp": "2024-01-10T08:30:00Z"
      },
      {
        "type": "procedure",
        "code": "93000",
        "description": "Electrocardiogram",
        "timestamp": "2024-01-10T09:00:00Z"
      }
    ],
    "lab_results": [
      {
        "name": "HbA1c",
        "value": 8.2,
        "unit": "%",
        "timestamp": "2024-01-10T07:00:00Z"
      },
      {
        "name": "eGFR",
        "value": 45,
        "unit": "mL/min/1.73m²",
        "timestamp": "2024-01-10T07:00:00Z"
      },
      {
        "name": "BNP",
        "value": 450,
        "unit": "pg/mL",
        "timestamp": "2024-01-10T07:30:00Z"
      }
    ],
    "medications": [
      {
        "name": "Metformin",
        "dose": "1000mg",
        "frequency": "BID",
        "route": "PO"
      },
      {
        "name": "Lisinopril",
        "dose": "10mg",
        "frequency": "QD",
        "route": "PO"
      },
      {
        "name": "Furosemide",
        "dose": "40mg",
        "frequency": "QD",
        "route": "PO"
      }
    ]
  }
}
```

## Step 2: Make API Request

### Using curl

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @patient_data.json
```

### Using Python requests

```python
import requests
import json

# Load patient data
with open('patient_data.json', 'r') as f:
    payload = json.load(f)

# Make prediction request
response = requests.post(
    'http://localhost:8000/predict',
    json=payload
)

# Check response
if response.status_code == 200:
    result = response.json()
    print(json.dumps(result, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### Using Python Client Library

```python
from code.model_factory.model_registry import ModelRegistry

# Load model
registry = ModelRegistry()
model = registry.get_model("readmission_v1")

# Prepare patient data
patient_data = {
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
        {"name": "eGFR", "value": 45, "unit": "mL/min/1.73m²"},
        {"name": "BNP", "value": 450, "unit": "pg/mL"}
    ],
    "medications": [
        {"name": "Metformin", "dose": "1000mg", "frequency": "BID"},
        {"name": "Lisinopril", "dose": "10mg", "frequency": "QD"},
        {"name": "Furosemide", "dose": "40mg", "frequency": "QD"}
    ]
}

# Generate prediction
prediction = model.predict(patient_data)

# Display results
print(f"\n=== Readmission Risk Prediction ===")
print(f"Patient ID: {patient_data['patient_id']}")
print(f"Risk Score: {prediction['risk']:.2%}")
print(f"Risk Level: {prediction['risk_level'].upper()}")
print(f"Confidence Interval: [{prediction['confidence_interval'][0]:.2%}, {prediction['confidence_interval'][1]:.2%}]")

# Show top risk factors
print(f"\nTop Risk Factors:")
for i, factor in enumerate(prediction['top_features'][:5], 1):
    print(f"  {i}. {factor}")

# Get explanation
explanation = model.explain(patient_data)
print(f"\n=== Feature Contributions (SHAP) ===")
for feature, contribution in list(explanation['feature_contributions'].items())[:5]:
    print(f"{feature}: {contribution:+.3f}")
```

## Step 3: Interpret Results

### Example Response

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
    "top_features": [
      "heart_failure_diagnosis",
      "age_65_plus",
      "elevated_bnp",
      "reduced_egfr",
      "diabetes_uncontrolled"
    ]
  },
  "explanations": {
    "method": "SHAP",
    "feature_contributions": {
      "heart_failure_diagnosis": 0.25,
      "age_65_plus": 0.15,
      "elevated_bnp": 0.12,
      "reduced_egfr": 0.1,
      "diabetes_uncontrolled": 0.08
    }
  },
  "uncertainty": {
    "confidence_interval": [0.65, 0.85],
    "standard_error": 0.05
  }
}
```

### Interpretation

**Risk Score**: 0.75 (75%)

- Patient has **high risk** of 30-day readmission
- Confidence interval: 65%-85%

**Top Risk Factors**:

1. **Heart failure diagnosis** (25% contribution)
2. **Age 65+** (15% contribution)
3. **Elevated BNP** (12% contribution)
4. **Reduced eGFR** (10% contribution)
5. **Uncontrolled diabetes** (8% contribution)

### Clinical Actions

For **high-risk** patients (>75%):

- Schedule follow-up within 7 days post-discharge
- Arrange home health services
- Perform medication reconciliation
- Assign care transition coach
- Educate on warning signs
- Provide emergency contact information

## Step 4: Log Prediction (Audit Trail)

```python
from code.compliance.phi_audit_logger import PHIAuditLogger

# Initialize audit logger
audit_logger = PHIAuditLogger(db_path="audit/phi_access.db")

# Log the prediction
audit_logger.log_prediction_request(
    patient_id="12345",
    user_id="dr.smith@hospital.org",
    model_used="readmission_v1",
    context="Discharge planning",
    timestamp=None  # Auto-generated
)

print("Prediction logged for HIPAA audit trail")
```

## Complete Working Example

```python
#!/usr/bin/env python3
"""
Complete example: Basic readmission risk prediction
"""

import requests
import json

def predict_readmission_risk(api_url, patient_data):
    """Make prediction request to Nexora API."""

    payload = {
        "model_name": "readmission_v1",
        "patient_data": patient_data
    }

    try:
        response = requests.post(
            f"{api_url}/predict",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def main():
    # API configuration
    API_URL = "http://localhost:8000"

    # Patient data
    patient = {
        "patient_id": "12345",
        "demographics": {
            "age": 68,
            "gender": "M",
            "race": "Caucasian"
        },
        "clinical_events": [
            {"type": "diagnosis", "code": "I50.9", "description": "Heart failure"},
            {"type": "diagnosis", "code": "E11.9", "description": "Type 2 diabetes"}
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

    # Make prediction
    print("Making prediction request...")
    result = predict_readmission_risk(API_URL, patient)

    if result:
        print("\n=== Readmission Risk Prediction ===")
        print(f"Patient ID: {patient['patient_id']}")
        print(f"Risk Score: {result['predictions']['risk']:.2%}")
        print(f"Risk Level: {result['predictions']['risk_level'].upper()}")
        print(f"\nTop Risk Factors:")
        for i, factor in enumerate(result['predictions']['top_features'][:5], 1):
            print(f"  {i}. {factor}")

        # Recommend actions based on risk level
        risk_level = result['predictions']['risk_level']
        print(f"\n=== Recommended Actions ({risk_level.upper()} RISK) ===")

        if risk_level == "high":
            print("- Schedule follow-up within 7 days")
            print("- Arrange home health services")
            print("- Medication reconciliation required")
            print("- Assign care transition coach")
        elif risk_level == "medium":
            print("- Schedule follow-up within 14 days")
            print("- Medication review recommended")
        else:
            print("- Standard discharge instructions")
            print("- Follow-up as needed")

if __name__ == "__main__":
    main()
```

## Run the Example

```bash
# Save as basic_prediction_example.py
python basic_prediction_example.py
```

## Expected Output

```
Making prediction request...

=== Readmission Risk Prediction ===
Patient ID: 12345
Risk Score: 75%
Risk Level: HIGH

Top Risk Factors:
  1. heart_failure_diagnosis
  2. age_65_plus
  3. elevated_bnp
  4. reduced_egfr
  5. diabetes_uncontrolled

=== Recommended Actions (HIGH RISK) ===
- Schedule follow-up within 7 days
- Arrange home health services
- Medication reconciliation required
- Assign care transition coach
```

## Next Steps

- Try [Batch Processing Example](batch_processing.md) for multiple patients
- Explore [FHIR Integration Example](fhir_integration.md) for EHR connectivity
- Learn about [Clinical Workflow Example](clinical_workflow.md) for discharge planning

## Troubleshooting

**Issue**: API returns 404

- Verify API is running: `curl http://localhost:8000/health`
- Check port: Default is 8000

**Issue**: 422 Validation Error

- Ensure all required fields are included
- Check field types match schema
- View interactive docs: http://localhost:8000/docs

**Issue**: Model not found

- Verify model name: `curl http://localhost:8000/models`
- Check model registry path

For more help, see [Troubleshooting Guide](../TROUBLESHOOTING.md).
