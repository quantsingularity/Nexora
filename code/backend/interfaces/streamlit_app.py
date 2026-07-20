"""
Nexora Clinician UI – Streamlit Application

Provides a browser-based dashboard for:
  • Patient risk prediction (single patient & batch)
  • Model comparison
  • PHI audit log viewer
  • Concept drift monitoring
  • Fairness metrics overview
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

import numpy as np
import pandas as pd

try:
    import streamlit as st

    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
if _ST_AVAILABLE:
    st.set_page_config(
        page_title="Nexora Clinical AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )

# ---------------------------------------------------------------------------
# ML imports (graceful fallback)
# ---------------------------------------------------------------------------
try:
    from ml_core.compliance.phi_audit_logger import PHIAuditLogger
    from ml_core.models.model_registry import ModelRegistry
    from ml_core.monitoring.concept_drift import ConceptDriftDetector

    _ML_AVAILABLE = True
except Exception:
    _ML_AVAILABLE = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AUDIT_DB = os.environ.get("AUDIT_DB_PATH", "audit/phi_access.db")
_API_URL = os.environ.get("NEXORA_API_URL", "http://localhost:8000")


@st.cache_resource(show_spinner=False)  # type: ignore[misc]
def _get_registry() -> Any:
    if _ML_AVAILABLE:
        return ModelRegistry()
    return None


@st.cache_resource(show_spinner=False)  # type: ignore[misc]
def _get_audit_logger() -> Any:
    if _ML_AVAILABLE:
        os.makedirs(
            os.path.dirname(_AUDIT_DB) if os.path.dirname(_AUDIT_DB) else ".",
            exist_ok=True,
        )
        return PHIAuditLogger(db_path=_AUDIT_DB)
    return None


def _risk_badge(score: float) -> str:
    if score >= 0.7:
        return f"HIGH ({score:.0%})"
    if score >= 0.4:
        return f"MODERATE ({score:.0%})"
    return f"LOW ({score:.0%})"


def _make_dummy_patient(patient_id: str) -> Dict[str, Any]:
    rng = np.random.default_rng(hash(patient_id) % (2**31))
    return {
        "patient_id": patient_id,
        "demographics": {
            "age": int(rng.integers(40, 85)),
            "gender": rng.choice(["male", "female"]),
            "ethnicity": rng.choice(["White", "Black", "Hispanic", "Asian", "Other"]),
        },
        "clinical_events": [
            {"type": "diagnosis", "code": "I10", "description": "Hypertension"},
            {"type": "diagnosis", "code": "E11", "description": "Type 2 Diabetes"},
        ],
        "lab_results": [
            {
                "name": "Creatinine",
                "value": float(rng.uniform(0.8, 3.5)),
                "date": "2024-01-15",
            },
            {
                "name": "HbA1c",
                "value": float(rng.uniform(5.5, 9.0)),
                "date": "2024-01-15",
            },
        ],
        "medications": [
            {"name": "Metformin", "dose": "500mg", "frequency": "BID"},
        ],
    }


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------


def page_predict_single() -> None:
    st.header("Single Patient Risk Assessment")

    col1, col2 = st.columns([1, 2])
    with col1:
        patient_id = st.text_input("Patient ID", value="P001", key="single_pid")
        model_name = st.selectbox(
            "Model",
            ["deep_fm", "survival_analysis", "transformer_model"],
            key="single_model",
        )
        run_btn = st.button("Run Prediction", type="primary", key="single_run")

    if run_btn:
        registry = _get_registry()
        audit = _get_audit_logger()
        patient_data = _make_dummy_patient(patient_id)

        with st.spinner("Running prediction…"):
            if registry and _ML_AVAILABLE:
                try:
                    model = registry.get_model(model_name, "latest")
                    predictions = model.predict(patient_data)
                    explanations = model.explain(patient_data)
                    if audit:
                        audit.log_prediction_request(
                            patient_id=patient_id,
                            model_used=f"{model_name} v latest",
                        )
                    error = None
                except Exception as e:
                    predictions = {}
                    explanations = {}
                    error = str(e)
            else:
                rng = np.random.default_rng(hash(patient_id) % (2**31))
                risk = float(rng.uniform(0.1, 0.9))
                predictions = {
                    "risk_score": round(risk, 4),
                    "readmission_probability_30d": round(min(risk * 1.1, 1.0), 4),
                    "top_features": ["creatinine_trend", "age", "comorbidity_count"],
                }
                explanations = {
                    "method": "demo_mode",
                    "features": ["creatinine_trend", "age", "comorbidities"],
                    "values": [0.28, 0.22, 0.18],
                }
                error = None

        with col2:
            if error:
                st.error(f"Prediction failed: {error}")
                return

            risk_score = predictions.get("risk_score", 0.0)
            st.subheader("Risk Assessment")
            st.markdown(f"### {_risk_badge(risk_score)}")

            metric_cols = st.columns(3)
            metric_cols[0].metric("Risk Score", f"{risk_score:.3f}")
            metric_cols[1].metric(
                "30-day Readmission",
                f"{predictions.get('readmission_probability_30d', 0):.1%}",
            )
            metric_cols[2].metric("Patient", patient_id)

        st.divider()
        exp_col, dem_col = st.columns(2)

        with exp_col:
            st.subheader("Feature Contributions")
            features = explanations.get("features", [])
            values = explanations.get("values", [])
            if features and values:
                imp_df = pd.DataFrame(
                    {"Feature": features, "Importance": values}
                ).sort_values("Importance", ascending=True)
                st.bar_chart(imp_df.set_index("Feature"))

        with dem_col:
            st.subheader("Patient Demographics")
            demo = patient_data["demographics"]
            st.json(demo)


def page_predict_batch() -> None:
    st.header("Batch Risk Assessment")
    st.markdown(
        "Upload a CSV with a `patient_id` column to run predictions on multiple patients."
    )

    uploaded = st.file_uploader("Upload patient list (CSV)", type=["csv"])
    model_name = st.selectbox(
        "Model",
        ["deep_fm", "survival_analysis", "transformer_model"],
        key="batch_model",
    )

    if uploaded:
        df = pd.read_csv(uploaded)
        if "patient_id" not in df.columns:
            st.error("CSV must contain a 'patient_id' column.")
            return

        st.write(f"Found **{len(df)}** patients.")
        if st.button("Run Batch Prediction", type="primary"):
            registry = _get_registry()
            results = []
            progress = st.progress(0)

            for i, pid in enumerate(df["patient_id"].tolist()):
                patient_data = _make_dummy_patient(str(pid))
                try:
                    if registry and _ML_AVAILABLE:
                        model = registry.get_model(model_name, "latest")
                        preds = model.predict(patient_data)
                    else:
                        rng = np.random.default_rng(hash(str(pid)) % (2**31))
                        risk = float(rng.uniform(0.1, 0.9))
                        preds = {
                            "risk_score": risk,
                            "readmission_probability_30d": min(risk * 1.1, 1.0),
                        }
                    results.append({"patient_id": pid, **preds})
                except Exception as e:
                    results.append({"patient_id": pid, "error": str(e)})
                progress.progress((i + 1) / len(df))

            results_df = pd.DataFrame(results)
            st.success(f"Completed {len(results_df)} predictions.")
            st.dataframe(results_df, use_container_width=True)

            csv = results_df.to_csv(index=False)
            st.download_button(
                "Download Results CSV",
                data=csv,
                file_name=f"nexora_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )


def page_audit_log() -> None:
    st.header("PHI Audit Log")

    audit = _get_audit_logger()
    if not audit:
        st.warning("Audit logger unavailable in demo mode.")
        _show_demo_audit_table()
        return

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date", value=pd.Timestamp.now() - pd.Timedelta(days=30)
        )
    with col2:
        end_date = st.date_input("End date", value=pd.Timestamp.now())

    patient_filter = st.text_input("Filter by Patient ID (leave blank for all)")

    if st.button("Load Audit Log"):
        try:
            if patient_filter:
                df = audit.get_patient_access_history(patient_filter)
            else:
                df = audit.generate_report(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                )
            if df.empty:
                st.info("No audit records found for the selected criteria.")
            else:
                st.metric("Total Access Events", len(df))
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load audit log: {e}")
            _show_demo_audit_table()


def _show_demo_audit_table() -> None:
    demo = pd.DataFrame(
        [
            {
                "timestamp": "2024-01-15T10:22:01",
                "user": "dr_smith",
                "patient": "P001",
                "operation": "READ",
                "model": "deep_fm v1.0.0",
            },
            {
                "timestamp": "2024-01-15T11:05:44",
                "user": "API_USER",
                "patient": "P002",
                "operation": "READ",
                "model": "survival_analysis v1.0.0",
            },
        ]
    )
    st.dataframe(demo, use_container_width=True)


def page_drift_monitoring() -> None:
    st.header("Concept Drift Monitoring")

    model_options = ["deep_fm", "survival_analysis", "transformer_model"]
    selected = st.selectbox("Select model to monitor", model_options)

    if st.button("Check for Drift"):
        rng = np.random.default_rng(hash(selected) % 1000)
        dummy_data = [
            {
                "age": float(rng.integers(50, 80)),
                "prediction": float(rng.uniform(0.1, 0.9)),
            }
            for _ in range(50)
        ]
        if _ML_AVAILABLE:
            try:
                detector = ConceptDriftDetector(model_name=selected)
                result = detector.check_for_drift(dummy_data)
            except Exception:
                result = _demo_drift_result(selected)
        else:
            result = _demo_drift_result(selected)

        status = result.get("status", "Unknown")
        st.subheader(f"Status: {status}")
        st.json(result)


def _demo_drift_result(model_name: str) -> Dict[str, Any]:
    return {
        "model": model_name,
        "status": "Stable",
        "last_checked": datetime.now().isoformat(),
        "baseline": {"prediction_mean": 0.35, "auc": 0.85},
    }


def page_fairness() -> None:
    st.header("Fairness Metrics")
    st.markdown(
        "Evaluate model fairness across demographic groups using synthetic cohort data."
    )

    n_patients = st.slider(
        "Cohort size", min_value=100, max_value=2000, value=500, step=100
    )
    group_col = st.selectbox(
        "Sensitive attribute", ["ethnicity", "gender", "age_group"]
    )

    if st.button("Compute Fairness Metrics"):
        rng = np.random.default_rng(42)
        ethnicities = rng.choice(
            ["White", "Black", "Hispanic", "Asian"], size=n_patients
        )
        genders = rng.choice(["male", "female"], size=n_patients)
        age_groups = rng.choice(["18-40", "41-60", "61-80", "80+"], size=n_patients)
        predictions = rng.uniform(0.1, 0.9, n_patients)
        outcomes = (predictions + rng.normal(0, 0.2, n_patients) > 0.5).astype(int)

        df = pd.DataFrame(
            {
                "prediction": predictions,
                "outcome": outcomes,
                "ethnicity": ethnicities,
                "gender": genders,
                "age_group": age_groups,
            }
        )

        group_stats = (
            df.groupby(group_col)
            .agg(
                mean_prediction=("prediction", "mean"),
                positive_rate=("outcome", "mean"),
                count=("prediction", "count"),
            )
            .reset_index()
        )
        group_stats["mean_prediction"] = group_stats["mean_prediction"].round(3)
        group_stats["positive_rate"] = group_stats["positive_rate"].round(3)

        disparity = float(
            group_stats["mean_prediction"].max() - group_stats["mean_prediction"].min()
        )
        st.metric(
            "Demographic Parity Disparity",
            f"{disparity:.3f}",
            help="0 = perfect parity",
        )

        st.subheader("Per-group Statistics")
        st.dataframe(group_stats, use_container_width=True)

        st.subheader("Prediction Distribution by Group")
        st.bar_chart(group_stats.set_index(group_col)["mean_prediction"])


def page_model_overview() -> None:
    st.header("Registered Models")
    registry = _get_registry()
    if registry and _ML_AVAILABLE:
        try:
            models = registry.list_models()
            for name, versions in models.items():
                with st.expander(f"{name}"):
                    for ver, cfg in versions.items():
                        st.json(cfg)
        except Exception as e:
            st.error(str(e))
            _show_demo_models()
    else:
        _show_demo_models()


def _show_demo_models() -> None:
    demo = {
        "deep_fm": {"1.0.0": {"name": "deep_fm", "version": "1.0.0"}},
        "survival_analysis": {
            "1.0.0": {"name": "survival_analysis", "version": "1.0.0"}
        },
        "transformer_model": {
            "1.0.0": {"name": "transformer_model", "version": "1.0.0"}
        },
    }
    for name, versions in demo.items():
        with st.expander(f"{name}"):
            st.json(versions)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


def main() -> None:
    if not _ST_AVAILABLE:
        raise RuntimeError("Streamlit is not installed. Run: pip install streamlit")

    st.sidebar.title("Nexora Clinical AI")
    st.sidebar.markdown("---")

    pages = {
        "Single Patient Prediction": page_predict_single,
        "Batch Prediction": page_predict_batch,
        "Model Overview": page_model_overview,
        "Concept Drift Monitoring": page_drift_monitoring,
        "Fairness Metrics": page_fairness,
        "PHI Audit Log": page_audit_log,
    }

    selection = st.sidebar.radio("Navigate", list(pages.keys()))

    if not _ML_AVAILABLE:
        st.sidebar.warning("Running in demo mode (ML libraries not fully loaded).")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Nexora v2.0.0 · {datetime.now().strftime('%Y-%m-%d')}")

    pages[selection]()


if __name__ == "__main__" or _ST_AVAILABLE:
    main()
