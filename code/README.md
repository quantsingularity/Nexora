# Nexora Clinical AI Platform

> HIPAA-compliant clinical decision support with fairness monitoring, explainability, and multi-model serving.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [ML Core Modules](#ml-core-modules)
- [Backend API](#backend-api)
- [Clinician UI](#clinician-ui)
- [Configuration](#configuration)
- [Testing](#testing)
- [Changelog v2.0.0](#changelog-v200)

---

## Overview

Nexora is a production-ready clinical AI platform providing:

- **Risk prediction** – readmission, mortality, and time-to-event models
- **Explainability** – SHAP-style permutation importance, LIME, counterfactuals
- **Fairness monitoring** – demographic parity, equal opportunity, calibration by group
- **HIPAA compliance** – PHI de-identification, audit logging, right-to-erasure
- **Concept drift detection** – statistical monitoring of feature and prediction distributions
- **Multi-modal serving** – REST API (FastAPI) and gRPC server
- **Clinician UI** – Streamlit dashboard for prediction, audit, and fairness inspection

---

## Project Structure

```
nexora/
├── backend/
│   ├── app/
│   │   ├── api/routes.py           ← All FastAPI route handlers
│   │   ├── core/config.py          ← Settings from environment variables
│   │   ├── models/prediction_log.py
│   │   └── schemas/clinical.py     ← Pydantic v2 request/response schemas
│   ├── interfaces/
│   │   └── streamlit_app.py        ← Clinician UI  [NEW]
│   ├── serving/
│   │   ├── rest_api.py             ← FastAPI app factory
│   │   └── grpc_server.py          ← gRPC prediction server  [NEW]
│   └── tests/api/test_rest_api.py
│
├── ml_core/                        ← Renamed from ml/
│   ├── compliance/phi_audit_logger.py
│   ├── config/
│   ├── explainability/             ← NEW
│   │   └── explainer.py            ← SHAP, LIME, attention, counterfactuals
│   ├── feature_store/              ← NEW
│   │   └── feature_store.py        ← Parquet-backed patient feature store
│   ├── models/
│   │   ├── base_model.py
│   │   ├── deep_fm.py
│   │   ├── fairness_metrics.py     ← Canonical copy (duplicate removed)
│   │   ├── model_calibration.py
│   │   ├── model_registry.py
│   │   ├── survival_analysis.py    ← Bug fixed
│   │   └── transformer_model.py
│   ├── monitoring/
│   │   ├── adverse_event_reporting.py
│   │   ├── clinical_metrics.py
│   │   └── concept_drift.py
│   ├── pipeline/
│   ├── tests/
│   │   ├── explainability/test_explainer.py   ← NEW
│   │   ├── test_feature_store.py              ← NEW
│   │   ├── test_artifact_store.py             ← NEW
│   │   └── ... (existing test suites)
│   ├── utils/
│   │   ├── fhir_connector.py
│   │   └── fhir_ops.py             ← Now exported via __init__
│   ├── validation/pipeline_validator.py
│   └── versioning/                 ← NEW
│       └── artifact_store.py       ← SHA-256 checksums + promotion workflow
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Quickstart

### Docker (recommended)

```bash
docker compose up --build
```

| Service      | URL                        |
| ------------ | -------------------------- |
| REST API     | http://localhost:8000      |
| API Docs     | http://localhost:8000/docs |
| Clinician UI | http://localhost:8501      |
| gRPC         | localhost:50051            |

### Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.serving.rest_api:app --reload --port 8000
```

---

## ML Core Modules

### Models

| Class                   | Framework                             |
| ----------------------- | ------------------------------------- |
| `DeepFMModel`           | TensorFlow (optional, numpy fallback) |
| `TransformerModel`      | PyTorch (optional, numpy fallback)    |
| `SurvivalAnalysisModel` | lifelines (optional, numpy fallback)  |
| `ModelCalibrator`       | scikit-learn                          |
| `FairnessEvaluator`     | pandas / sklearn                      |

### Explainability (new)

```python
from ml_core.explainability import ModelExplainer

explainer = ModelExplainer(
    predict_fn=model.predict_proba,
    feature_names=feature_names,
    background_data=X_train,
)
result = explainer.explain(patient_vector, method="permutation_shap")
print(result.top_features(n=5))

cf = explainer.explain(patient_vector, method="counterfactual")
print(cf.counterfactuals)  # minimal changes that flip the prediction

df = explainer.global_importance(X_test)  # mean |SHAP| across cohort
```

Methods: `permutation_shap`, `lime`, `attention`, `counterfactual`.

### Feature Store (new)

```python
from ml_core.feature_store import FeatureStore

store = FeatureStore("data/feature_store")
store.upsert("P001", {"age": 65, "creatinine": 1.2})
row   = store.get("P001")
recent = store.get_recent(days=7)
store.delete_patient("P001")   # HIPAA right-to-erasure
```

### Artifact Versioning (new)

```python
from ml_core.versioning import ModelArtifactStore, ModelStage

store = ModelArtifactStore("artifacts")
store.register("deep_fm", "1.1.0", "trained.h5",
               metrics={"auc": 0.89}, hyperparameters={"layers": [256, 128]})
store.promote("deep_fm", "1.1.0", ModelStage.PRODUCTION)
# Previous production version auto-archived
```

---

## Backend API

| Method   | Path                         | Description          |
| -------- | ---------------------------- | -------------------- |
| `GET`    | `/health`                    | Health check         |
| `GET`    | `/models`                    | List models          |
| `POST`   | `/predict`                   | Single prediction    |
| `POST`   | `/predict/batch`             | Batch prediction     |
| `POST`   | `/fhir/patient/{id}/predict` | Predict from FHIR    |
| `GET`    | `/metrics`                   | Cohort metrics       |
| `GET`    | `/audit/patient/{id}`        | PHI audit history    |
| `DELETE` | `/models/{name}/{version}`   | Remove model version |

---

## Clinician UI

Streamlit dashboard at http://localhost:8501:

- Single patient risk prediction with feature attribution chart
- Batch prediction with CSV upload/download
- Model registry browser
- Concept drift monitoring per model
- Fairness metrics by demographic group
- PHI audit log with date-range and patient filters

---

## Configuration

| Variable              | Default                      | Description                  |
| --------------------- | ---------------------------- | ---------------------------- |
| `PORT`                | `8000`                       | REST API port                |
| `GRPC_PORT`           | `50051`                      | gRPC port                    |
| `AUDIT_DB_PATH`       | `audit/phi_access.db`        | SQLite audit DB              |
| `FHIR_SERVER_URL`     | `http://mock-fhir-server/R4` | FHIR R4 base URL             |
| `FEATURE_STORE_PATH`  | `data/feature_store`         | Feature store root           |
| `ARTIFACT_STORE_PATH` | `artifacts`                  | Artifact store root          |
| `LOG_LEVEL`           | `INFO`                       | Logging level                |
| `CORS_ORIGINS`        | `*`                          | Comma-separated CORS origins |

---

## Testing

```bash
pytest ml_core/tests/ backend/tests/ -v --cov=ml_core --cov=backend

# Individual suites
pytest ml_core/tests/explainability/
pytest ml_core/tests/test_feature_store.py
pytest ml_core/tests/test_artifact_store.py
pytest ml_core/tests/model_tests/
```

---

## Changelog v2.0.0

**Breaking**

- `ml/` renamed to `ml_core/` - all imports updated

**Bug fixes**

- `survival_analysis.py` - silent dead assignment via `locals()[val]=…` fixed with direct variable assignment
- Duplicate `fairness_metrics.py` removed from `monitoring/` (canonical copy in `models/`)

**New modules**

- `ml_core/explainability/` - SHAP-style, LIME, attention, counterfactuals
- `ml_core/feature_store/` - Parquet-backed feature persistence
- `ml_core/versioning/` - SHA-256 artifact store with promotion workflow
- `backend/serving/grpc_server.py` - gRPC server (was missing, referenced in docker-compose)
- `backend/interfaces/streamlit_app.py` - Clinician UI (was missing, referenced in docker-compose)

**Improvements**

- `backend/app/` stubs fully implemented (schemas, config, models, routes)
- `rest_api.py` refactored - routes extracted to `api/routes.py`
- `fhir_ops.py` exposed via `utils/__init__.py`
- All `__init__.py` files now export `__all__`
- `docker-compose.yml` - fixed UI path, added `nexora-artifacts` volume
- `requirements.txt` - added `streamlit`, `pytest-asyncio`
- New tests: `test_explainer.py`, `test_feature_store.py`, `test_artifact_store.py`
- Removed all `__pycache__` and `.pytest_cache` directories
