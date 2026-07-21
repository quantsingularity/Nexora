# Nexora Clinical AI Platform

HIPAA-aware clinical decision support with authenticated patient management, fairness monitoring, explainability, and multi-model serving.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [Backend API](#backend-api)
- [ML Core Modules](#ml-core-modules)
- [Clinician UI](#clinician-ui)
- [gRPC Service](#grpc-service)
- [Configuration](#configuration)
- [Testing](#testing)

---

## Overview

Nexora is a clinical AI platform providing:

- **Authentication and accounts** - clinician registration, login, and profile management with JWT sessions
- **Patient management** - a searchable patient roster with full CRUD, backed by SQLite
- **Risk prediction** - readmission, mortality, and time-to-event models, computed per patient and recomputable on demand
- **Dashboard analytics** - cohort risk distribution, admissions trends, and model performance in one summary endpoint
- **Alerts** - notifications generated from current patient risk data
- **Explainability** - SHAP-style permutation importance, LIME, attention, and counterfactuals
- **Fairness monitoring** - demographic parity, equal opportunity, and calibration by group
- **HIPAA-aware compliance** - PHI de-identification, audit logging, and right-to-erasure
- **Concept drift detection** - statistical monitoring of feature and prediction distributions
- **Multi-modal serving** - REST API (FastAPI), gRPC server, and a Streamlit clinician UI

---

## Project Structure

```
code/
├── backend/
│   ├── app/            # API routes, core config/security, data models, schemas
│   ├── interfaces/     # Streamlit clinician UI
│   ├── serving/        # FastAPI app factory and gRPC server
│   └── tests/
│
├── ml_core/
│   ├── compliance/      # PHI audit logging
│   ├── explainability/  # SHAP, LIME, attention, counterfactuals
│   ├── feature_store/   # Parquet-backed feature persistence
│   ├── models/          # Prediction models, calibration, fairness, registry
│   ├── monitoring/       # Clinical metrics, concept drift, adverse events
│   ├── pipeline/         # FHIR ETL, de-identification, feature engineering
│   ├── utils/            # FHIR client and healthcare metric helpers
│   ├── validation/       # Pipeline validation utilities
│   ├── versioning/       # Model artifact store
│   └── tests/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

See [Backend API](#backend-api) and [ML Core Modules](#ml-core-modules) below for what lives in each file.

---

## Quickstart

### Docker (recommended)

```bash
docker compose up --build
```

| Service      | URL                        |
| ------------ | -------------------------- |
| REST API     | http://localhost:8000      |
| API docs     | http://localhost:8000/docs |
| Clinician UI | http://localhost:8501      |
| gRPC         | localhost:50051            |

### Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.serving.rest_api:app --reload --port 8000
```

On first run, the API creates `data/nexora_app.db` and seeds 45 demo patients automatically, so there's nothing else to set up before exploring the endpoints.

---

## Backend API

All endpoints are served with no path prefix (for example `/auth/login`, not `/api/auth/login`). Endpoints marked **Auth** require an `Authorization: Bearer <token>` header.

### System, models, and prediction

| Method   | Path                         | Auth | Description                        |
| -------- | ---------------------------- | :--: | ---------------------------------- |
| `GET`    | `/health`                    |      | Health check                       |
| `GET`    | `/models`                    |      | List registered models             |
| `DELETE` | `/models/{name}/{version}`   |      | Remove a model version             |
| `POST`   | `/predict`                   |      | Single prediction                  |
| `POST`   | `/predict/batch`             |      | Batch prediction                   |
| `POST`   | `/fhir/patient/{id}/predict` |      | Predict from a FHIR patient record |
| `GET`    | `/metrics`                   |      | Cohort clinical metrics            |
| `GET`    | `/audit/patient/{id}`        |      | PHI audit history for a patient    |

### Authentication

| Method  | Path                    | Auth | Description                       |
| ------- | ----------------------- | :--: | --------------------------------- |
| `POST`  | `/auth/register`        |      | Create a clinician account        |
| `POST`  | `/auth/login`           |      | Sign in and receive a JWT         |
| `GET`   | `/auth/me`              | Yes  | Get the current user's profile    |
| `PATCH` | `/auth/me`              | Yes  | Update the current user's profile |
| `POST`  | `/auth/change-password` | Yes  | Change password                   |
| `POST`  | `/auth/logout`          | Yes  | Sign out                          |

### Patients

| Method   | Path                            | Auth | Description                              |
| -------- | ------------------------------- | :--: | ---------------------------------------- |
| `GET`    | `/patients`                     | Yes  | List patients, with search and paging    |
| `POST`   | `/patients`                     | Yes  | Add a patient and compute its risk score |
| `GET`    | `/patients/{id}`                | Yes  | Get full patient detail                  |
| `PUT`    | `/patients/{id}`                | Yes  | Update patient details                   |
| `DELETE` | `/patients/{id}`                | Yes  | Remove a patient                         |
| `POST`   | `/patients/{id}/recompute-risk` | Yes  | Recompute a patient's risk score         |

Risk scores come from the same model registry used by `/predict`, so a patient's score is always consistent with the standalone prediction endpoint. Patients are banded as **high** (score >= 0.75), **medium** (>= 0.40), or **low** (below 0.40).

### Dashboard and alerts

| Method  | Path                       | Auth | Description                        |
| ------- | -------------------------- | :--: | ---------------------------------- |
| `GET`   | `/dashboard/summary`       | Yes  | Cohort stats, risk mix, and trends |
| `GET`   | `/notifications`           | Yes  | List alerts and unread count       |
| `PATCH` | `/notifications/{id}/read` | Yes  | Mark one alert as read             |
| `POST`  | `/notifications/read-all`  | Yes  | Mark all alerts as read            |

---

## ML Core Modules

| Area           | Module                                   | Purpose                                                            |
| -------------- | ---------------------------------------- | ------------------------------------------------------------------ |
| Models         | `models.deep_fm`                         | Factorization-machine model for 30-day readmission risk            |
| Models         | `models.transformer_model`               | Sequence transformer over longitudinal clinical events             |
| Models         | `models.survival_analysis`               | Time-to-event model for readmission likelihood                     |
| Models         | `models.model_registry`                  | Versioned model lookup and lifecycle management                    |
| Models         | `models.model_calibration`               | Isotonic regression, Platt scaling, and beta calibration           |
| Models         | `models.fairness_metrics`                | Demographic parity, equal opportunity, calibration by group        |
| Explainability | `explainability.explainer`               | Permutation SHAP, LIME, attention, and counterfactual explanations |
| Feature store  | `feature_store.feature_store`            | Parquet-backed patient feature persistence with an in-memory cache |
| Versioning     | `versioning.artifact_store`              | Checksummed model artifacts with a staging-to-production workflow  |
| Monitoring     | `monitoring.clinical_metrics`            | Cohort-level clinical performance metrics                          |
| Monitoring     | `monitoring.concept_drift`               | Statistical drift detection for features and predictions           |
| Monitoring     | `monitoring.adverse_event_reporting`     | Structured adverse event capture                                   |
| Pipeline       | `pipeline.clinical_etl`                  | Extracts from FHIR and transforms into model-ready features        |
| Pipeline       | `pipeline.icd10_encoder`                 | ICD-10 diagnosis code encoding                                     |
| Pipeline       | `pipeline.temporal_features`             | Time-windowed feature extraction                                   |
| Pipeline       | `pipeline.hipaa_compliance.deidentifier` | Safe Harbor PHI de-identification                                  |
| Pipeline       | `pipeline.hipaa_compliance.phi_detector` | Detects likely PHI fields ahead of de-identification               |
| Compliance     | `compliance.phi_audit_logger`            | Logs every PHI access for HIPAA audit trails                       |
| Utilities      | `utils.fhir_connector`                   | FHIR R4 server client                                              |
| Utilities      | `utils.healthcare_metrics`               | Shared clinical calculation helpers                                |
| Validation     | `validation.pipeline_validator`          | End-to-end pipeline validation utilities                           |

---

## Clinician UI

Streamlit dashboard at http://localhost:8501, with one page per task:

- Single patient risk assessment with feature attribution
- Batch prediction with CSV upload and download
- Registered model browser
- Concept drift monitoring per model
- Fairness metrics by demographic group
- PHI audit log with date-range and patient filters

---

## gRPC Service

`backend.serving.grpc_server` exposes a prediction service on port `50051` (configurable via `GRPC_PORT`):

| Method        | Description                               |
| ------------- | ----------------------------------------- |
| `Predict`     | Run a prediction for a single patient     |
| `HealthCheck` | Service health status                     |
| `ListModels`  | List models available to the gRPC service |

The server falls back to a stub mode when `grpcio` isn't installed, so importing the module never fails even without the optional dependency.

---

## Configuration

| Variable              | Default                      | Description                                                    |
| --------------------- | ---------------------------- | -------------------------------------------------------------- |
| `HOST`                | `0.0.0.0`                    | REST API bind address                                          |
| `PORT`                | `8000`                       | REST API port                                                  |
| `GRPC_PORT`           | `50051`                      | gRPC port                                                      |
| `GRPC_MAX_WORKERS`    | `10`                         | gRPC thread pool size                                          |
| `AUDIT_DB_PATH`       | `audit/phi_access.db`        | SQLite PHI audit log                                           |
| `APP_DB_PATH`         | `data/nexora_app.db`         | SQLite accounts and patients database                          |
| `FHIR_SERVER_URL`     | `http://mock-fhir-server/R4` | FHIR R4 base URL                                               |
| `FEATURE_STORE_PATH`  | `data/feature_store`         | Feature store root                                             |
| `ARTIFACT_STORE_PATH` | `artifacts`                  | Artifact store root                                            |
| `JWT_SECRET_KEY`      | development-only default     | Signing key for session tokens; set a real value in production |
| `JWT_ALGORITHM`       | `HS256`                      | JWT signing algorithm                                          |
| `JWT_EXPIRE_MINUTES`  | `10080` (7 days)             | Session token lifetime                                         |
| `CORS_ORIGINS`        | `*`                          | Comma-separated allowed CORS origins                           |
| `LOG_LEVEL`           | `INFO`                       | Logging level                                                  |
| `DEBUG`               | `false`                      | Enables `uvicorn --reload`-friendly settings                   |
| `NEXORA_API_URL`      | `http://localhost:8000`      | API base URL used by the Streamlit UI                          |

---

## Testing

```bash
pytest ml_core/tests/ backend/tests/ -v --cov=ml_core --cov=backend

# Individual suites
pytest backend/tests/api/test_auth_and_patients.py
pytest ml_core/tests/explainability/
pytest ml_core/tests/test_feature_store.py
pytest ml_core/tests/test_artifact_store.py
pytest ml_core/tests/model_tests/
```

| Suite                        | Location                                                        | Covers                                           |
| ---------------------------- | --------------------------------------------------------------- | ------------------------------------------------ |
| REST API core                | `backend/tests/api/test_rest_api.py`                            | Health, models, prediction, FHIR, metrics, audit |
| REST API accounts            | `backend/tests/api/test_auth_and_patients.py`                   | Auth, patients, dashboard, notifications         |
| Explainability               | `ml_core/tests/explainability/`                                 | SHAP, LIME, attention, counterfactuals           |
| Model factory                | `ml_core/tests/model_factory/`                                  | Model registry lookup and lifecycle              |
| Model behavior               | `ml_core/tests/model_tests/`                                    | Calibration, fairness, predictive equality       |
| Monitoring                   | `ml_core/tests/monitoring/`                                     | Adverse events, clinical metrics                 |
| Compliance                   | `ml_core/tests/compliance/`                                     | PHI audit logging                                |
| Data pipeline                | `ml_core/tests/data_pipeline/`                                  | Clinical ETL                                     |
| Clinical validation          | `ml_core/tests/clinical_tests/`                                 | Data validation, FHIR ingestion                  |
| Feature store and versioning | `ml_core/tests/test_feature_store.py`, `test_artifact_store.py` | Feature persistence, artifact promotion          |
| Utilities                    | `ml_core/tests/utils/`                                          | FHIR connector, healthcare metrics               |
