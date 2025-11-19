"""
Documentation for HIPAA-Compliant Nexora Implementation

This document provides an overview of the HIPAA compliance implementation
and validation for the Nexora clinical data pipeline and models.
"""

## Overview

The Nexora project has been enhanced with comprehensive HIPAA compliance measures,
focusing on proper de-identification of Protected Health Information (PHI) in the
clinical data pipeline and readmission prediction models. This implementation
follows the Safe Harbor method specified in the HIPAA Privacy Rule (45 CFR 164.514(b)(2)).

## Implementation Details

### 1. HIPAA-Compliant De-identification

A robust de-identification module has been implemented that handles all 18 identifiers
specified in the HIPAA Safe Harbor method:

- Names
- Geographic subdivisions smaller than a state
- All elements of dates related to an individual
- Telephone numbers
- Fax numbers
- Email addresses
- Social Security numbers
- Medical record numbers
- Health plan beneficiary numbers
- Account numbers
- Certificate/license numbers
- Vehicle identifiers and serial numbers
- Device identifiers and serial numbers
- Web URLs
- IP addresses
- Biometric identifiers
- Full-face photographs and comparable images
- Any other unique identifying number, characteristic, or code

The implementation includes:

- **PHIDeidentifier**: Core class for de-identifying PHI in various data formats
- **DeidentificationConfig**: Configuration class for customizing de-identification behavior
- **PHIDetector**: Utility for detecting potential PHI in clinical data

### 2. Pipeline Integration

The de-identification module has been integrated into the clinical data pipeline:

- **HIPAACompliantHealthcareETL**: Enhanced ETL pipeline with de-identification steps
- **DeidentifyFHIRDoFn**: Apache Beam DoFn for de-identifying FHIR bundles
- **DeidentifyDataFrameDoFn**: Apache Beam DoFn for de-identifying pandas DataFrames

### 3. Validation and Testing

Comprehensive validation and testing mechanisms have been implemented:

- **PipelineValidator**: Validates both functionality and HIPAA compliance
- **AutomatedValidator**: Automates the validation process across multiple datasets and models
- **Test Suite**: Unit and integration tests for all components

## Usage

### De-identification Configuration

```python
from src.data_pipeline.hipaa_compliance.deidentifier import DeidentificationConfig

# Create configuration
config = DeidentificationConfig(
    hash_patient_ids=True,
    remove_names=True,
    remove_addresses=True,
    remove_dates_of_birth=True,
    remove_contact_info=True,
    remove_mrns=True,
    remove_ssn=True,
    remove_device_ids=True,
    age_threshold=89,
    shift_dates=True,
    date_shift_strategy='patient',
    max_date_shift_days=365,
    k_anonymity_threshold=5
)
```

### De-identifying Data

```python
from src.data_pipeline.hipaa_compliance.deidentifier import PHIDeidentifier

# Create de-identifier
deidentifier = PHIDeidentifier(config)

# De-identify DataFrame
deidentified_df = deidentifier.deidentify_dataframe(
    df,
    patient_id_col='patient_id',
    phi_cols=['name', 'dob', 'address', 'phone', 'email']
)

# De-identify FHIR bundle
deidentified_bundle = deidentifier.deidentify_fhir_bundle(fhir_bundle)
```

### Using the HIPAA-Compliant Pipeline

```python
from src.data_pipeline.hipaa_compliance.integration import create_hipaa_compliant_etl

# Create HIPAA-compliant ETL pipeline
etl = create_hipaa_compliant_etl(
    deidentification_config=config,
    patient_id_col='patient_id',
    phi_cols=['name', 'dob', 'address', 'phone', 'email']
)

# Use in Apache Beam pipeline
with beam.Pipeline() as p:
    data = p | beam.io.ReadFromText('data.json') | beam.Map(json.loads)
    processed = data | etl
    processed | beam.io.WriteToText('processed_data.json')
```

### Running Validation

```python
from src.validation.pipeline_validator import AutomatedValidator

# Create validator
validator = AutomatedValidator(
    data_dir='data',
    model_dir='models',
    output_dir='validation_results'
)

# Run validation
results = validator.run_automated_validation()

# Check overall status
print(f"Overall validation status: {results['overall_status']}")
```

### Running Tests

```bash
# Run all tests
python -m src.validation.run_tests --output-dir test_results

# Run specific test module
python -m unittest src.validation.tests.test_hipaa_compliance
```

## Compliance Considerations

1. **Regular Validation**: Run the validation scripts regularly to ensure continued compliance.
2. **Configuration Updates**: Update the de-identification configuration as needed based on changes in data or regulations.
3. **Documentation**: Maintain documentation of all de-identification and validation processes.
4. **Audit Trail**: Keep records of validation results for compliance audits.
5. **Staff Training**: Ensure all staff are trained on HIPAA compliance requirements and the use of these tools.

## Future Enhancements

1. **Advanced De-identification**: Implement more sophisticated de-identification techniques such as differential privacy.
2. **Automated Monitoring**: Develop continuous monitoring of PHI leakage in production.
3. **Compliance Reporting**: Enhance reporting capabilities for compliance officers.
4. **Integration with Security Framework**: Integrate with broader security and compliance frameworks.

---

For any questions or issues, please contact the development team.
