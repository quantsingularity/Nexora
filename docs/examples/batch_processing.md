# Example: Batch Processing

This example demonstrates how to process multiple patients in batch mode for efficient risk stratification.

## Use Case

Process an entire patient cohort (100-10,000 patients) to identify high-risk patients before discharge.

## Prerequisites

- Nexora installation complete
- Patient data file (JSON or CSV)
- Model trained and registered

## Step 1: Prepare Batch Input File

### JSON Format (`patients_cohort.json`)

```json
[
  {
    "patient_id": "PT001",
    "demographics": { "age": 72, "gender": "F" },
    "clinical_events": [{ "type": "diagnosis", "code": "I50.9" }],
    "lab_results": [{ "name": "BNP", "value": 580, "unit": "pg/mL" }]
  },
  {
    "patient_id": "PT002",
    "demographics": { "age": 65, "gender": "M" },
    "clinical_events": [{ "type": "diagnosis", "code": "J44.1" }],
    "lab_results": [{ "name": "FEV1", "value": 55, "unit": "%" }]
  },
  {
    "patient_id": "PT003",
    "demographics": { "age": 58, "gender": "F" },
    "clinical_events": [{ "type": "diagnosis", "code": "E11.9" }],
    "lab_results": [{ "name": "HbA1c", "value": 9.1, "unit": "%" }]
  }
]
```

### CSV Format (`patients_cohort.csv`)

```csv
patient_id,age,gender,diagnosis_codes,bnp,hba1c
PT001,72,F,I50.9,580,
PT002,65,M,J44.1,,
PT003,58,F,E11.9,,9.1
```

## Step 2: Run Batch Scoring Script

### Basic Usage

```bash
python scripts/batch_scoring.py \
  --input data/patients_cohort.json \
  --output results/predictions.json \
  --model readmission_v1
```

### Advanced Options

```bash
python scripts/batch_scoring.py \
  --input data/large_cohort.json \
  --output results/risk_scores.json \
  --model readmission_v1 \
  --config config/clinical_config.yaml \
  --batch-size 500 \
  --verbose \
  --parallel
```

**Arguments**:

- `--input`: Input file path (JSON/CSV)
- `--output`: Output file path
- `--model`: Model name to use
- `--config`: Configuration file
- `--batch-size`: Number of patients per batch (default: 100)
- `--verbose`: Enable detailed logging
- `--parallel`: Use parallel processing

## Step 3: Output Format

### Example Output (`predictions.json`)

```json
{
  "metadata": {
    "model_name": "readmission_v1",
    "model_version": "1.0.0",
    "timestamp": "2024-01-15T14:30:00Z",
    "total_patients": 3,
    "processing_time_seconds": 2.5
  },
  "predictions": [
    {
      "patient_id": "PT001",
      "risk": 0.82,
      "risk_level": "high",
      "confidence_interval": [0.72, 0.92],
      "top_features": ["heart_failure", "age_65_plus", "elevated_bnp"]
    },
    {
      "patient_id": "PT002",
      "risk": 0.45,
      "risk_level": "medium",
      "confidence_interval": [0.35, 0.55],
      "top_features": ["copd", "age_65_plus", "reduced_fev1"]
    },
    {
      "patient_id": "PT003",
      "risk": 0.28,
      "risk_level": "low",
      "confidence_interval": [0.18, 0.38],
      "top_features": ["diabetes", "uncontrolled_hba1c"]
    }
  ],
  "summary": {
    "high_risk_count": 1,
    "medium_risk_count": 1,
    "low_risk_count": 1,
    "mean_risk": 0.52,
    "median_risk": 0.45
  }
}
```

## Step 4: Python Script for Batch Processing

### Custom Batch Processing Script

```python
#!/usr/bin/env python3
"""
Custom batch processing script with progress tracking
"""

import json
from pathlib import Path
from tqdm import tqdm
from code.model_factory.model_registry import ModelRegistry

def load_patient_data(input_file):
    """Load patient data from JSON or CSV."""
    if input_file.endswith('.json'):
        with open(input_file, 'r') as f:
            return json.load(f)
    elif input_file.endswith('.csv'):
        import pandas as pd
        df = pd.read_csv(input_file)
        return df.to_dict('records')
    else:
        raise ValueError("Unsupported file format")

def batch_predict(patients, model, batch_size=100):
    """Process patients in batches with progress bar."""
    results = []

    for i in tqdm(range(0, len(patients), batch_size), desc="Processing batches"):
        batch = patients[i:i+batch_size]

        for patient in batch:
            try:
                prediction = model.predict(patient)
                results.append({
                    "patient_id": patient['patient_id'],
                    "risk": prediction['risk'],
                    "risk_level": prediction['risk_level'],
                    "top_features": prediction['top_features']
                })
            except Exception as e:
                print(f"Error processing patient {patient['patient_id']}: {e}")
                results.append({
                    "patient_id": patient['patient_id'],
                    "error": str(e)
                })

    return results

def stratify_patients(predictions):
    """Stratify patients by risk level."""
    high_risk = [p for p in predictions if p.get('risk_level') == 'high']
    medium_risk = [p for p in predictions if p.get('risk_level') == 'medium']
    low_risk = [p for p in predictions if p.get('risk_level') == 'low']

    return {
        'high': high_risk,
        'medium': medium_risk,
        'low': low_risk
    }

def main():
    # Configuration
    INPUT_FILE = "data/patients_cohort.json"
    OUTPUT_FILE = "results/predictions.json"
    MODEL_NAME = "readmission_v1"
    BATCH_SIZE = 100

    # Load model
    print(f"Loading model: {MODEL_NAME}")
    registry = ModelRegistry()
    model = registry.get_model(MODEL_NAME)

    # Load patients
    print(f"Loading patients from {INPUT_FILE}")
    patients = load_patient_data(INPUT_FILE)
    print(f"Loaded {len(patients)} patients")

    # Process in batches
    print("Processing predictions...")
    predictions = batch_predict(patients, model, BATCH_SIZE)

    # Stratify by risk
    stratified = stratify_patients(predictions)

    # Save results
    output = {
        "metadata": {
            "model_name": MODEL_NAME,
            "total_patients": len(patients),
            "processed_patients": len(predictions)
        },
        "predictions": predictions,
        "summary": {
            "high_risk_count": len(stratified['high']),
            "medium_risk_count": len(stratified['medium']),
            "low_risk_count": len(stratified['low'])
        },
        "stratified": stratified
    }

    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    # Print summary
    print(f"\n=== Processing Complete ===")
    print(f"Total patients: {len(patients)}")
    print(f"High risk: {len(stratified['high'])} ({len(stratified['high'])/len(patients)*100:.1f}%)")
    print(f"Medium risk: {len(stratified['medium'])} ({len(stratified['medium'])/len(patients)*100:.1f}%)")
    print(f"Low risk: {len(stratified['low'])} ({len(stratified['low'])/len(patients)*100:.1f}%)")
    print(f"\nResults saved to: {OUTPUT_FILE}")

    # List high-risk patients
    if stratified['high']:
        print(f"\n=== High-Risk Patients (Intervention Required) ===")
        for patient in stratified['high'][:10]:  # Show top 10
            print(f"Patient {patient['patient_id']}: Risk {patient['risk']:.2%}")

if __name__ == "__main__":
    main()
```

## Step 5: Parallel Processing for Large Cohorts

```python
from multiprocessing import Pool
from functools import partial

def process_patient_batch(batch, model_name):
    """Process a batch of patients (for parallel execution)."""
    from code.model_factory.model_registry import ModelRegistry

    registry = ModelRegistry()
    model = registry.get_model(model_name)

    results = []
    for patient in batch:
        prediction = model.predict(patient)
        results.append({
            "patient_id": patient['patient_id'],
            "risk": prediction['risk'],
            "risk_level": prediction['risk_level']
        })

    return results

def parallel_batch_predict(patients, model_name, n_workers=4, batch_size=100):
    """Process patients in parallel using multiple cores."""
    # Split into batches
    batches = [patients[i:i+batch_size] for i in range(0, len(patients), batch_size)]

    # Process in parallel
    with Pool(processes=n_workers) as pool:
        process_func = partial(process_patient_batch, model_name=model_name)
        batch_results = pool.map(process_func, batches)

    # Flatten results
    results = [item for sublist in batch_results for item in sublist]
    return results

# Usage
results = parallel_batch_predict(
    patients=patient_list,
    model_name="readmission_v1",
    n_workers=8,
    batch_size=250
)
```

## Step 6: Generate Cohort Report

```python
def generate_cohort_report(predictions, output_file="cohort_report.html"):
    """Generate HTML report for cohort analysis."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Extract risk scores
    risks = [p['risk'] for p in predictions if 'risk' in p]

    # Create visualizations
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1. Risk distribution histogram
    axes[0, 0].hist(risks, bins=20, edgecolor='black')
    axes[0, 0].set_title('Risk Score Distribution')
    axes[0, 0].set_xlabel('Risk Score')
    axes[0, 0].set_ylabel('Count')

    # 2. Risk level pie chart
    risk_levels = [p['risk_level'] for p in predictions if 'risk_level' in p]
    risk_counts = {
        'high': risk_levels.count('high'),
        'medium': risk_levels.count('medium'),
        'low': risk_levels.count('low')
    }
    axes[0, 1].pie(risk_counts.values(), labels=risk_counts.keys(), autopct='%1.1f%%')
    axes[0, 1].set_title('Risk Level Distribution')

    plt.tight_layout()
    plt.savefig('cohort_analysis.png')

    # Generate HTML report
    html = f"""
    <html>
    <head><title>Cohort Risk Analysis</title></head>
    <body>
        <h1>Readmission Risk Analysis</h1>
        <h2>Summary Statistics</h2>
        <ul>
            <li>Total Patients: {len(predictions)}</li>
            <li>High Risk: {risk_counts['high']}</li>
            <li>Medium Risk: {risk_counts['medium']}</li>
            <li>Low Risk: {risk_counts['low']}</li>
            <li>Mean Risk: {sum(risks)/len(risks):.2%}</li>
        </ul>
        <img src="cohort_analysis.png" />
    </body>
    </html>
    """

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"Report generated: {output_file}")
```

## Performance Benchmarks

|     Cohort Size | Sequential Time | Parallel Time (8 cores) | Speedup |
| --------------: | --------------: | ----------------------: | ------: |
|    100 patients |          12 sec |                   3 sec |      4x |
|  1,000 patients |           2 min |                  25 sec |    4.8x |
| 10,000 patients |          18 min |                   4 min |    4.5x |

## Next Steps

- Generate [Cohort Report](cohort_reporting.md)
- Integrate with [Clinical Workflow](clinical_workflow.md)
- Setup [Automated Daily Runs](automation.md)

## Troubleshooting

**Issue**: Out of memory with large cohorts

- Reduce batch size: `--batch-size 50`
- Use streaming mode (process one at a time)
- Increase system memory

**Issue**: Slow processing

- Enable parallel processing
- Use GPU if available
- Reduce model complexity

For more help, see [Troubleshooting Guide](../TROUBLESHOOTING.md).
