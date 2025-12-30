# Example: FHIR Integration

This example demonstrates how to integrate Nexora with FHIR servers for seamless EHR connectivity.

## Use Case

Pull patient data directly from FHIR-compliant EHR system and generate readmission predictions without manual data entry.

## Prerequisites

- FHIR R4 server accessible (test or production)
- OAuth2 credentials (if authentication required)
- Patient ID in FHIR server

## Step 1: Configure FHIR Connection

### Environment Variables

```bash
# .env
FHIR_SERVER_URL=https://fhir-server.hospital.org/R4
FHIR_AUTH_TYPE=oauth2
FHIR_TOKEN=your-oauth2-bearer-token
```

### Configuration File

```yaml
# config/clinical_config.yaml
data:
  fhir:
    base_url: https://fhir-server.hospital.org/R4
    page_count: 1000
    timeout_seconds: 30
    retry_attempts: 3
    auth:
      type: oauth2
      token_url: https://auth.hospital.org/oauth2/token
      client_id: nexora-client
      # client_secret: Set in environment variable
```

## Step 2: API-Based FHIR Integration

### Using REST API Endpoint

```bash
# Direct prediction from FHIR patient ID
curl -X POST "http://localhost:8000/fhir/patient/example-patient-123/predict?model_name=readmission_v1" \
  -H "Authorization: Bearer YOUR_NEXORA_TOKEN"
```

### Python Requests Example

```python
import requests

API_URL = "http://localhost:8000"
PATIENT_ID = "example-patient-123"
MODEL_NAME = "readmission_v1"

response = requests.post(
    f"{API_URL}/fhir/patient/{PATIENT_ID}/predict",
    params={"model_name": MODEL_NAME},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

if response.status_code == 200:
    prediction = response.json()
    print(f"Risk: {prediction['predictions']['risk']:.2%}")
else:
    print(f"Error: {response.text}")
```

## Step 3: Direct FHIR Connector Usage

### Initialize FHIR Connector

```python
from code.utils.fhir_connector import FHIRConnector
from code.model_factory.model_registry import ModelRegistry

# Initialize FHIR connector
fhir_client = FHIRConnector(
    base_url="https://fhir-server.hospital.org/R4",
    auth_token="your-oauth2-token"
)

# Load prediction model
registry = ModelRegistry()
model = registry.get_model("readmission_v1")
```

### Fetch Patient Data

```python
# Get patient demographics and clinical data
patient_id = "example-patient-123"

try:
    # Fetch FHIR resources
    patient_bundle = fhir_client.get_patient_data(patient_id)

    print(f"Fetched data for patient: {patient_id}")
    print(f"Resources retrieved: {len(patient_bundle.entry)}")

except Exception as e:
    print(f"Error fetching patient data: {e}")
```

### Transform FHIR to Model Input

```python
from code.utils.fhir_ops import FHIRClinicalConnector

# Initialize transformer
connector = FHIRClinicalConnector()

# Transform FHIR Bundle to model input format
model_input = connector.transform_fhir_to_model_input(patient_bundle)

print("Transformed patient data:")
print(f"  Age: {model_input['demographics']['age']}")
print(f"  Gender: {model_input['demographics']['gender']}")
print(f"  Diagnoses: {len(model_input['clinical_events'])}")
```

### Generate Prediction

```python
# Make prediction
prediction = model.predict(model_input)

print("\n=== Readmission Risk Prediction ===")
print(f"Risk Score: {prediction['risk']:.2%}")
print(f"Risk Level: {prediction['risk_level'].upper()}")

print("\nTop Risk Factors:")
for i, factor in enumerate(prediction['top_features'][:5], 1):
    print(f"  {i}. {factor}")
```

## Step 4: Complete FHIR Integration Example

```python
#!/usr/bin/env python3
"""
Complete FHIR integration example with error handling
"""

import os
from code.utils.fhir_connector import FHIRConnector
from code.utils.fhir_ops import FHIRClinicalConnector
from code.model_factory.model_registry import ModelRegistry
from code.compliance.phi_audit_logger import PHIAuditLogger

def predict_from_fhir(patient_id, model_name="readmission_v1", user_id="system"):
    """Generate prediction from FHIR patient data."""

    # Initialize components
    fhir_client = FHIRConnector(
        base_url=os.getenv("FHIR_SERVER_URL"),
        auth_token=os.getenv("FHIR_TOKEN")
    )

    connector = FHIRClinicalConnector()
    registry = ModelRegistry()
    audit_logger = PHIAuditLogger()

    try:
        # 1. Fetch patient data from FHIR server
        print(f"Fetching data for patient: {patient_id}")
        patient_bundle = fhir_client.get_patient_data(patient_id)

        # 2. Transform FHIR data to model input
        print("Transforming FHIR data...")
        model_input = connector.transform_fhir_to_model_input(patient_bundle)

        # 3. Load model
        print(f"Loading model: {model_name}")
        model = registry.get_model(model_name)

        # 4. Generate prediction
        print("Generating prediction...")
        prediction = model.predict(model_input)
        explanation = model.explain(model_input)

        # 5. Log for audit trail
        audit_logger.log_prediction_request(
            patient_id=patient_id,
            user_id=user_id,
            model_used=model_name,
            context="FHIR integration"
        )

        # 6. Return results
        return {
            "patient_id": patient_id,
            "prediction": prediction,
            "explanation": explanation,
            "data_source": "FHIR",
            "success": True
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "patient_id": patient_id,
            "error": str(e),
            "success": False
        }

def main():
    # Configuration
    PATIENT_IDS = [
        "example-patient-123",
        "example-patient-456",
        "example-patient-789"
    ]

    # Process each patient
    results = []
    for patient_id in PATIENT_IDS:
        print(f"\n{'='*60}")
        result = predict_from_fhir(patient_id, user_id="dr.smith")
        results.append(result)

        if result['success']:
            pred = result['prediction']
            print(f"\nPatient: {patient_id}")
            print(f"Risk: {pred['risk']:.2%} ({pred['risk_level'].upper()})")
            print(f"Top factors: {', '.join(pred['top_features'][:3])}")

    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n{'='*60}")
    print(f"Processed {len(results)} patients")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

if __name__ == "__main__":
    main()
```

## Step 5: Batch FHIR Processing

```python
def batch_predict_from_fhir(patient_ids, model_name="readmission_v1"):
    """Process multiple patients from FHIR in batch."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm

    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_patient = {
            executor.submit(predict_from_fhir, patient_id, model_name): patient_id
            for patient_id in patient_ids
        }

        # Process completed tasks with progress bar
        for future in tqdm(as_completed(future_to_patient), total=len(patient_ids)):
            patient_id = future_to_patient[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing {patient_id}: {e}")
                results.append({
                    "patient_id": patient_id,
                    "error": str(e),
                    "success": False
                })

    return results

# Usage
patient_list = ["PT001", "PT002", "PT003", ...]  # List of FHIR patient IDs
results = batch_predict_from_fhir(patient_list)
```

## Step 6: SMART-on-FHIR Launch

### Launch Context

```python
from code.utils.fhir_ops import SMARTLaunchHandler

# Initialize SMART launch handler
smart_handler = SMARTLaunchHandler(
    client_id="nexora-client-id",
    client_secret=os.getenv("SMART_CLIENT_SECRET"),
    redirect_uri="https://nexora.hospital.org/smart/callback"
)

# Handle launch request
@app.get("/launch")
async def smart_launch(launch: str, iss: str):
    """Handle SMART-on-FHIR launch request."""
    auth_url = smart_handler.get_authorization_url(
        launch=launch,
        iss=iss,
        scope="patient/*.read launch"
    )
    return RedirectResponse(url=auth_url)

# Handle callback
@app.get("/smart/callback")
async def smart_callback(code: str, state: str):
    """Handle OAuth2 callback."""
    token_response = smart_handler.exchange_code_for_token(code)
    access_token = token_response['access_token']
    patient_id = token_response['patient']

    # Use token to fetch patient data and predict
    result = predict_from_fhir(
        patient_id=patient_id,
        auth_token=access_token
    )

    return result
```

## Step 7: FHIR Search and Query

### Search for Patients by Criteria

```python
# Search for patients with heart failure diagnosis
search_params = {
    "condition": "I50.9",  # Heart failure ICD-10 code
    "active": "true"
}

patients = fhir_client.search_resources(
    resource_type="Patient",
    params=search_params
)

print(f"Found {len(patients.entry)} patients with heart failure")

# Process each patient
for patient in patients.entry:
    patient_id = patient.resource.id
    prediction = predict_from_fhir(patient_id)
    # ... process prediction
```

### Query Observations

```python
# Get recent lab results for patient
observations = fhir_client.search_resources(
    resource_type="Observation",
    params={
        "patient": patient_id,
        "category": "laboratory",
        "_count": 100,
        "_sort": "-date"
    }
)

print(f"Found {len(observations.entry)} lab results")
```

## Troubleshooting FHIR Integration

### Issue: Authentication Failed

```python
# Test FHIR connection
try:
    metadata = fhir_client.get_capability_statement()
    print("FHIR server connection successful")
    print(f"Server version: {metadata.fhirVersion}")
except Exception as e:
    print(f"Connection failed: {e}")
    print("Check FHIR_SERVER_URL and FHIR_TOKEN")
```

### Issue: Patient Not Found

```python
# Verify patient exists
try:
    patient_resource = fhir_client.read_resource("Patient", patient_id)
    print(f"Patient found: {patient_resource.id}")
except Exception as e:
    print(f"Patient not found: {e}")
```

### Issue: Missing Required Data

```python
# Validate transformed data
def validate_model_input(model_input):
    """Check if all required fields are present."""
    required_fields = ['patient_id', 'demographics', 'clinical_events']

    for field in required_fields:
        if field not in model_input:
            raise ValueError(f"Missing required field: {field}")

    if not model_input['clinical_events']:
        raise ValueError("No clinical events found")

    return True

# Use before prediction
try:
    validate_model_input(model_input)
    prediction = model.predict(model_input)
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Performance Tips

1. **Use connection pooling** for multiple requests
2. **Cache FHIR resources** to reduce API calls
3. **Process in parallel** for batch operations
4. **Implement retry logic** for transient failures
5. **Monitor rate limits** on FHIR server

## Next Steps

- Explore [EHR Alert Integration](ehr_integration.md)
- Learn about [Clinical Workflow](clinical_workflow.md)
- Setup [Automated Monitoring](monitoring_setup.md)

## Resources

- [HL7 FHIR R4 Specification](https://www.hl7.org/fhir/R4/)
- [SMART-on-FHIR Documentation](https://docs.smarthealthit.org/)
- [Nexora FHIR Connector API](../API.md#fhir-integration)
