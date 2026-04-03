# Configuration Directory

## Overview

The configuration directory contains essential configuration files that control various aspects of the Nexora system. This directory serves as a centralized location for all configuration parameters, ensuring consistent settings across the application and making it easier to modify system behavior without changing code.

## Directory Structure

```
config/
├── deid_rules.yaml
├── feature_configs/
│   ├── diagnosis_groups.json
│   └── medication_mappings.csv
└── model_configs/
    ├── deepfm_params.yaml
    └── xgb_hyperparameters.json
```

## Contents Description

### Root Files

- **deid_rules.yaml**: Contains rules for de-identification of Protected Health Information (PHI) in compliance with HIPAA regulations. These rules define patterns for identifying and masking sensitive patient information such as names, addresses, and medical record numbers.

### Subdirectories

#### feature_configs/

This subdirectory contains configuration files related to feature engineering and data transformation:

- **diagnosis_groups.json**: Defines groupings of diagnosis codes (likely ICD-10) into clinically meaningful categories. This helps in reducing dimensionality and improving model interpretability by grouping related diagnoses together.

- **medication_mappings.csv**: Maps medication names to standardized codes or categories. This file likely contains mappings between different medication naming conventions (e.g., brand names to generic names) or groupings of medications by therapeutic class.

#### model_configs/

This subdirectory contains configuration files for machine learning models:

- **deepfm_params.yaml**: Configuration parameters for the DeepFM (Deep Factorization Machine) model, which is likely used for patient risk prediction. Parameters may include learning rate, embedding dimensions, network architecture, and training settings.

- **xgb_hyperparameters.json**: Hyperparameters for XGBoost models, which are gradient boosting models commonly used for clinical prediction tasks. Parameters likely include tree depth, learning rate, regularization settings, and other model-specific configurations.

## Usage

Configuration files in this directory are loaded by various components of the Nexora system at runtime. Modifying these files allows for adjusting system behavior without recompiling code:

1. To modify de-identification rules, edit the `deid_rules.yaml` file.
2. To update feature engineering parameters, modify files in the `feature_configs/` directory.
3. To tune machine learning models, adjust parameters in the `model_configs/` directory.

## Best Practices

1. **Version Control**: Always commit configuration changes to version control with clear commit messages explaining the rationale.
2. **Testing**: Test configuration changes in a development environment before deploying to production.
3. **Documentation**: Document any non-obvious parameter settings and their effects on system behavior.
4. **Validation**: Use the validation tools in the `tests/` directory to ensure configuration changes don't break system functionality.
5. **Backup**: Create backups of configuration files before making significant changes.

## Related Components

- The configuration files in this directory are primarily used by components in the `src/data_pipeline/` and `src/model_factory/` directories.
- The de-identification rules are used by the HIPAA compliance module in `src/data_pipeline/hipaa_compliance/`.
- Model configurations are used by the corresponding model implementations in `src/model_factory/`.
