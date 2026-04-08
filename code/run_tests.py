#!/usr/bin/env python3
"""
Nexora test runner.

Uses stdlib unittest — no pytest dependency required.
Pytest is also fully supported if installed: pytest tests/

Run with:
    python3 run_tests.py          # all tests
    python3 run_tests.py -v       # verbose
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
class TestPHIAuditLogger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        from compliance.phi_audit_logger import PHIAuditLogger

        self.logger = PHIAuditLogger(db_path=os.path.join(self.tmp, "audit.db"))

    def tearDown(self):
        self.logger.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_log_and_retrieve(self):
        self.logger.log_prediction_request("P001", user_id="u1", model_used="m1")
        df = self.logger.get_patient_access_history("P001")
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["patient"], "P001")

    def test_column_aliases(self):
        self.logger.log_access("admin", "COL", "Res", "READ", "Just", "mod")
        df = self.logger.get_patient_access_history("COL")
        for col in ["user", "patient", "resource", "operation", "reason", "model"]:
            self.assertIn(col, df.columns, f"Missing: {col}")

    def test_log_access_fields(self):
        self.logger.log_access("adm", "FT", "DiagReport", "WRITE", "Research", "deepfm")
        row = self.logger.get_patient_access_history("FT").iloc[0]
        self.assertEqual(row["resource"], "DiagReport")
        self.assertEqual(row["operation"], "WRITE")
        self.assertEqual(row["reason"], "Research")
        self.assertEqual(row["model"], "deepfm")

    def test_report_columns(self):
        from datetime import datetime, timedelta, timezone

        self.logger.log_prediction_request("RPT")
        start = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()
        df = self.logger.generate_report(start, end)
        for c in [
            "timestamp",
            "user",
            "patient",
            "resource",
            "operation",
            "reason",
            "model",
        ]:
            self.assertIn(c, df.columns)

    def test_multiple_logs(self):
        for i in range(5):
            self.logger.log_prediction_request("M", user_id=f"u{i}", model_used="m")
        self.assertEqual(len(self.logger.get_patient_access_history("M")), 5)

    def test_empty_history(self):
        self.assertEqual(len(self.logger.get_patient_access_history("GHOST")), 0)

    def test_operation_is_read(self):
        self.logger.log_prediction_request("OP")
        self.assertEqual(
            self.logger.get_patient_access_history("OP").iloc[0]["operation"], "READ"
        )

    def test_persistence(self):
        path = os.path.join(self.tmp, "persist.db")
        from compliance.phi_audit_logger import PHIAuditLogger

        lg = PHIAuditLogger(db_path=path)
        lg.log_prediction_request("PERSIST")
        lg.close()
        lg2 = PHIAuditLogger(db_path=path)
        self.assertEqual(len(lg2.get_patient_access_history("PERSIST")), 1)
        lg2.close()


# ─────────────────────────────────────────────────────────────────────────────
class TestModelRegistry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        from model_factory.model_registry import ModelRegistry

        self.reg = ModelRegistry(registry_path=os.path.join(self.tmp, "reg.json"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _model(self):
        from model_factory.transformer_model import TransformerModel

        return TransformerModel(
            {
                "name": "t",
                "version": "1.0",
                "vocab_size": 50,
                "d_model": 8,
                "nhead": 2,
                "num_layers": 1,
                "dim_feedforward": 16,
            }
        )

    def test_default_has_models(self):
        self.assertGreater(len(self.reg.list_models()), 0)
        self.assertIn("transformer_model", self.reg.list_models())

    def test_register_retrieve(self):
        m = self._model()
        self.reg.register_model("t", "1.0", m)
        self.assertIs(self.reg.get_model("t", "1.0"), m)

    def test_latest_alias(self):
        m = self._model()
        self.reg.register_model("t", "1.0", m)
        self.assertIsNotNone(self.reg.get_model("t", "latest"))

    def test_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.reg.get_model("ghost", "1.0")

    def test_version_not_found_raises(self):
        m = self._model()
        self.reg.register_model("t", "1.0", m)
        with self.assertRaises(ValueError):
            self.reg.get_model("t", "99.0")

    def test_list_excludes_latest(self):
        m = self._model()
        self.reg.register_model("t", "1.0", m)
        self.assertNotIn("latest", self.reg.list_models().get("t", {}))

    def test_persistence(self):
        from model_factory.model_registry import ModelRegistry

        path = os.path.join(self.tmp, "p.json")
        r = ModelRegistry(registry_path=path)
        r.register_model("x", "1.0", "m.pkl", config={"name": "x", "version": "1.0"})
        r2 = ModelRegistry(registry_path=path)
        self.assertIn("x", r2.metadata)

    def test_delete(self):
        m = self._model()
        self.reg.register_model("t", "1.0", m)
        self.reg.delete_model("t", "1.0")
        with self.assertRaises(Exception):
            self.reg.get_model("t", "1.0")

    def test_delete_ghost_raises(self):
        with self.assertRaises(ValueError):
            self.reg.delete_model("ghost", "1.0")

    def test_get_deep_fm(self):
        m = self.reg.get_model("deep_fm", "latest")
        self.assertIn(
            "risk_score",
            m.predict({"patient_id": "P", "demographics": {}, "clinical_events": []}),
        )

    def test_get_survival(self):
        m = self.reg.get_model("survival_analysis", "latest")
        self.assertIn(
            "risk_score",
            m.predict({"patient_id": "P", "demographics": {}, "clinical_events": []}),
        )

    def test_get_transformer(self):
        m = self.reg.get_model("transformer_model", "latest")
        self.assertIn(
            "risk_score",
            m.predict({"patient_id": "P", "demographics": {}, "clinical_events": []}),
        )

    def test_multiple_versions(self):
        from model_factory.transformer_model import TransformerModel

        cfg = {
            "name": "t",
            "vocab_size": 50,
            "d_model": 8,
            "nhead": 2,
            "num_layers": 1,
            "dim_feedforward": 16,
        }
        self.reg.register_model(
            "mv", "1.0", TransformerModel({**cfg, "version": "1.0"})
        )
        self.reg.register_model(
            "mv", "2.0", TransformerModel({**cfg, "version": "2.0"})
        )
        listed = self.reg.list_models()
        self.assertIn("1.0", listed["mv"])
        self.assertIn("2.0", listed["mv"])

    def test_unimplemented_raises(self):
        with self.assertRaises(Exception):
            self.reg.get_model("no_such_model_xyz", "latest")


# ─────────────────────────────────────────────────────────────────────────────
class TestTransformerModel(unittest.TestCase):
    def setUp(self):
        from model_factory.transformer_model import TransformerModel

        self.m = TransformerModel(
            {
                "name": "t",
                "version": "1.0",
                "vocab_size": 100,
                "d_model": 16,
                "nhead": 2,
                "num_layers": 1,
                "dim_feedforward": 32,
            }
        )

    def _p(self, pid="P"):
        return {"patient_id": pid, "demographics": {}, "clinical_events": []}

    def test_predict_dict(self):
        self.assertIsInstance(self.m.predict(self._p()), dict)

    def test_risk_score_bounds(self):
        s = self.m.predict(self._p())["risk_score"]
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 1)

    def test_uncertainty_ordered(self):
        ci = self.m.predict(self._p())["uncertainty"]["confidence_interval"]
        self.assertLessEqual(ci[0], ci[1])

    def test_deterministic(self):
        self.assertEqual(
            self.m.predict(self._p("X"))["risk_score"],
            self.m.predict(self._p("X"))["risk_score"],
        )

    def test_explain_has_method(self):
        self.assertIn("method", self.m.explain(self._p()))

    def test_train_no_crash(self):
        self.m.train(None)


# ─────────────────────────────────────────────────────────────────────────────
class TestDeepFMModel(unittest.TestCase):
    def setUp(self):
        from model_factory.deep_fm import DeepFMModel

        self.m = DeepFMModel(
            {
                "name": "dfm",
                "version": "1.0",
                "num_features": 10,
                "deep_layers": [16, 8],
            }
        )

    def _p(self):
        return {"patient_id": "P", "demographics": {}, "clinical_events": []}

    def test_predict_bounds(self):
        s = self.m.predict(self._p())["risk_score"]
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 1)

    def test_explain_has_method(self):
        self.assertIn("method", self.m.explain(self._p()))

    def test_train_no_crash(self):
        self.m.train(None)


# ─────────────────────────────────────────────────────────────────────────────
class TestSurvivalModel(unittest.TestCase):
    def setUp(self):
        from model_factory.survival_analysis import SurvivalAnalysisModel

        self.m = SurvivalAnalysisModel({"name": "s", "version": "1.0"})

    def _p(self):
        return {"patient_id": "P", "demographics": {}, "clinical_events": []}

    def test_predict_keys(self):
        r = self.m.predict(self._p())
        for k in ["risk_score", "survival_probability_30d", "median_survival_days"]:
            self.assertIn(k, r)

    def test_probability_bounds(self):
        r = self.m.predict(self._p())
        for k in [
            "survival_probability_30d",
            "survival_probability_90d",
            "survival_probability_365d",
        ]:
            self.assertGreaterEqual(r[k], 0)
            self.assertLessEqual(r[k], 1)

    def test_explain_has_method(self):
        self.assertIn("method", self.m.explain(self._p()))

    def test_train_no_crash(self):
        self.m.train(None)


# ─────────────────────────────────────────────────────────────────────────────
class TestModelCalibrator(unittest.TestCase):
    def setUp(self):
        from model_factory.model_calibration import ModelCalibrator

        self.c = ModelCalibrator()
        rng = np.random.default_rng(42)
        self.yt = rng.integers(0, 2, 300).astype(float)
        self.yp = np.clip(rng.normal(0.4, 0.2, 300), 0.01, 0.99)

    def _check(self, out):
        self.assertEqual(len(out), len(self.yp))
        self.assertTrue((out >= 0).all() and (out <= 1).all())

    def test_isotonic(self):
        self._check(self.c.calibrate(self.yp, self.yt, "isotonic"))

    def test_platt(self):
        self._check(self.c.calibrate(self.yp, self.yt, "platt"))

    def test_beta(self):
        self._check(self.c.calibrate(self.yp, self.yt, "beta"))

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.c.calibrate(self.yp, self.yt, "magic")

    def test_by_group(self):
        df = pd.DataFrame(
            {
                "g": np.random.choice(["A", "B"], len(self.yp)),
                "p": self.yp,
                "o": self.yt,
            }
        )
        r = self.c.calculate_calibration_by_group(df, "p", "o", "g")
        self.assertIn("calibration_by_group", r)
        for g in ["A", "B"]:
            self.assertIn("brier_score_before", r["calibration_by_group"][g])


# ─────────────────────────────────────────────────────────────────────────────
class TestFairnessEvaluator(unittest.TestCase):
    def setUp(self):
        from model_factory.fairness_metrics import FairnessEvaluator

        self.ev = FairnessEvaluator()
        rng = np.random.default_rng(1)
        n = 400
        self.df = pd.DataFrame(
            {
                "group": np.random.choice(["A", "B"], n),
                "outcome": rng.integers(0, 2, n),
                "prediction": np.clip(rng.normal(0.3, 0.15, n), 0.01, 0.99),
            }
        )

    def test_demographic_parity(self):
        r = self.ev.calculate_demographic_parity(self.df, "prediction", "group")
        self.assertIn("demographic_parity", r)
        self.assertGreaterEqual(r["demographic_parity"], 0)

    def test_equal_opportunity(self):
        r = self.ev.calculate_equal_opportunity(
            self.df, "prediction", "outcome", "group"
        )
        self.assertIn("true_positive_rates", r)

    def test_equalized_odds(self):
        r = self.ev.calculate_equalized_odds(self.df, "prediction", "outcome", "group")
        self.assertIn("false_positive_rates", r)

    def test_predictive_parity(self):
        self.assertIn(
            "predictive_parity",
            self.ev.calculate_predictive_parity(
                self.df, "prediction", "outcome", "group"
            ),
        )

    def test_calibration_by_group(self):
        self.assertIn(
            "brier_scores",
            self.ev.calculate_calibration_by_group(
                self.df, "prediction", "outcome", "group"
            ),
        )

    def test_report_keys(self):
        r = self.ev.generate_fairness_report(self.df, "prediction", "outcome", "group")
        for k in [
            "demographic_parity",
            "equal_opportunity",
            "equalized_odds",
            "predictive_parity",
            "calibration_by_group",
        ]:
            self.assertIn(k, r)

    def test_reweighting(self):
        r = self.ev.improve_fairness_with_reweighting(
            self.df, "prediction", "outcome", "group"
        )
        self.assertLessEqual(r["fairness_after"], r["fairness_before"] + 1e-9)

    def test_optimize_eo(self):
        r = self.ev.optimize_thresholds_for_equal_opportunity(
            self.df, "prediction", "outcome", "group"
        )
        self.assertLessEqual(
            r["equal_opportunity_after"], r["equal_opportunity_before"] + 0.01
        )

    def test_cross_validate(self):
        r = self.ev.cross_validate_fairness(
            self.df, "prediction", "outcome", "group", cv=3
        )
        self.assertEqual(len(r["fold_results"]), 3)

    def test_across_thresholds(self):
        r = self.ev.calculate_fairness_across_thresholds(
            self.df, "prediction", "outcome", "group", [0.3, 0.5, 0.7]
        )
        self.assertEqual(len(r["demographic_parity"]), 3)

    def test_export(self):
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "r.json")
            self.ev.export_fairness_report(
                self.ev.generate_fairness_report(
                    self.df, "prediction", "outcome", "group"
                ),
                path,
            )
            with open(path) as f:
                loaded = json.load(f)
            self.assertIn("demographic_parity", loaded)
        finally:
            shutil.rmtree(tmp)

    def test_plot_roc(self):
        self.assertIsNotNone(
            self.ev.plot_roc_curves_by_group(self.df, "prediction", "outcome", "group")
        )

    def test_adversarial_debiasing(self):
        r = self.ev.mock_adversarial_debiasing(
            np.random.randn(100, 5),
            np.random.randint(0, 2, 100),
            np.random.randint(0, 2, 100),
        )
        self.assertIn("debiased_predictions", r)


# ─────────────────────────────────────────────────────────────────────────────
class TestDataValidator(unittest.TestCase):
    def setUp(self):
        from data_pipeline.data_validation import DataValidator

        self.v = DataValidator()
        self.df = pd.DataFrame(
            {
                "patient_id": ["P001", "P002", "P003"],
                "age": pd.array([45, 67, 32], dtype=object),
                "gender": ["M", "F", "M"],
                "readmission": [0, 1, 0],
                "mortality": [0, 0, 0],
            }
        )
        self.schema = {
            "patient_id": {"type": "string", "required": True, "unique": True},
            "age": {"type": "integer", "required": True, "min": 0, "max": 120},
            "gender": {
                "type": "category",
                "required": True,
                "categories": ["M", "F", "O"],
            },
            "readmission": {"type": "boolean", "required": True},
            "mortality": {"type": "boolean", "required": True},
        }

    def test_schema_valid(self):
        self.assertTrue(self.v.validate_schema(self.df, self.schema)["valid"])

    def test_schema_missing(self):
        self.assertFalse(
            self.v.validate_schema(self.df.drop(columns=["age"]), self.schema)["valid"]
        )

    def test_schema_out_of_range(self):
        bad = self.df.copy()
        bad["age"] = bad["age"].astype(object)
        bad.loc[0, "age"] = 200
        self.assertFalse(self.v.validate_schema(bad, self.schema)["valid"])

    def test_schema_bad_category(self):
        bad = self.df.copy()
        bad.loc[0, "gender"] = "Z"
        self.assertFalse(self.v.validate_schema(bad, self.schema)["valid"])

    def test_schema_duplicate_unique(self):
        dup = pd.concat([self.df, self.df.iloc[:1]], ignore_index=True)
        self.assertFalse(self.v.validate_schema(dup, self.schema)["valid"])

    def test_temporal_ok(self):
        df = self.df.copy()
        df["s"] = pd.to_datetime("2023-01-01")
        df["e"] = pd.to_datetime("2023-01-10")
        self.assertTrue(
            self.v.validate_relationships(
                df,
                [{"type": "temporal", "first": "s", "second": "e", "relation": "<="}],
            )["valid"]
        )

    def test_temporal_violated(self):
        df = self.df.copy()
        df["s"] = pd.to_datetime("2023-01-10")
        df["e"] = pd.to_datetime("2023-01-01")
        self.assertFalse(
            self.v.validate_relationships(
                df,
                [{"type": "temporal", "first": "s", "second": "e", "relation": "<="}],
            )["valid"]
        )

    def test_logical_ok(self):
        self.assertTrue(
            self.v.validate_relationships(
                self.df,
                [
                    {
                        "type": "logical",
                        "condition": "mortality==1",
                        "implication": "readmission==0",
                    }
                ],
            )["valid"]
        )

    def test_logical_violated(self):
        bad = self.df.copy()
        bad.loc[0, "mortality"] = 1
        bad.loc[0, "readmission"] = 1
        self.assertFalse(
            self.v.validate_relationships(
                bad,
                [
                    {
                        "type": "logical",
                        "condition": "mortality==1",
                        "implication": "readmission==0",
                    }
                ],
            )["valid"]
        )

    def test_outliers_iqr(self):
        df = pd.DataFrame({"v": [1, 2, 2, 2, 3, 3, 100]})
        self.assertGreater(len(self.v.detect_outliers(df, ["v"])["outliers"]["v"]), 0)

    def test_outliers_zscore(self):
        df = pd.DataFrame({"v": [10.0] * 50 + [1000.0]})
        self.assertGreater(
            len(
                self.v.detect_outliers(df, ["v"], method="z-score", threshold=2.0)[
                    "outliers"
                ]["v"]
            ),
            0,
        )

    def test_outliers_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.v.detect_outliers(pd.DataFrame({"v": [1]}), ["v"], method="bad")

    def test_missing(self):
        bad = self.df.copy()
        bad.loc[0, "gender"] = None
        r = self.v.check_missing_values(bad)
        self.assertTrue(r["has_missing"])
        self.assertEqual(r["missing_counts"]["gender"], 1)

    def test_no_duplicates(self):
        self.assertFalse(
            self.v.check_duplicates(self.df, ["patient_id"])["has_duplicates"]
        )

    def test_duplicates_found(self):
        self.assertTrue(
            self.v.check_duplicates(
                pd.concat([self.df, self.df.iloc[:1]], ignore_index=True),
                ["patient_id"],
            )["has_duplicates"]
        )

    def test_icd10_valid(self):
        self.assertTrue(
            self.v.validate_icd10_codes(pd.Series(["A01.0", "B20", "I10"]))["valid"]
        )

    def test_icd10_invalid(self):
        self.assertFalse(
            self.v.validate_icd10_codes(pd.Series(["A01.0", "XYZ"]))["valid"]
        )

    def test_date_ranges_valid(self):
        df = pd.DataFrame({"d": pd.to_datetime(["2023-06-01"])})
        self.assertTrue(
            self.v.validate_date_ranges(df, "d", "2023-01-01", "2023-12-31")["valid"]
        )

    def test_date_ranges_invalid(self):
        df = pd.DataFrame({"d": pd.to_datetime(["2022-01-01"])})
        self.assertFalse(
            self.v.validate_date_ranges(df, "d", "2023-01-01", "2023-12-31")["valid"]
        )

    def test_consistency(self):
        r = self.v.validate_consistency(
            self.df, [{"name": "r", "condition": "age>0", "expected": "age<200"}]
        )
        self.assertTrue(r["valid"])

    def test_report_structure(self):
        r = self.v.generate_validation_report(
            self.df,
            schema=self.schema,
            outlier_columns=["age"],
            consistency_rules=[
                {"name": "r", "condition": "age>0", "expected": "age<200"}
            ],
        )
        for k in [
            "schema_validation",
            "relationship_validation",
            "missing_values",
            "outliers",
            "duplicates",
            "consistency",
            "summary",
        ]:
            self.assertIn(k, r)
        self.assertIn("valid", r["summary"])
        self.assertIn("error_count", r["summary"])


# ─────────────────────────────────────────────────────────────────────────────
class TestClinicalETL(unittest.TestCase):
    def setUp(self):
        from data_pipeline.clinical_etl import ClinicalETL

        self.etl = ClinicalETL()
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _p(self, pid):
        return {
            "patient_id": pid,
            "demographics": {"gender": "M", "birthDate": "1970-01-01"},
            "clinical_events": [
                {"type": "diagnosis", "code": "I10", "date": "2023-01-01"}
            ],
            "lab_results": [
                {
                    "name": "Creatinine",
                    "value": 1.1,
                    "unit": "mg/dL",
                    "date": "2023-06-01",
                }
            ],
            "medications": [],
        }

    def test_empty(self):
        df = self.etl.transform([])
        self.assertEqual(len(df), 0)

    def test_single(self):
        df = self.etl.transform([self._p("P001")])
        self.assertEqual(len(df), 1)
        self.assertIn("patient_id", df.columns)

    def test_multiple(self):
        df = self.etl.transform([self._p(f"P{i:03d}") for i in range(5)])
        self.assertEqual(len(df), 5)

    def test_no_labs(self):
        df = self.etl.transform(
            [
                {
                    "patient_id": "X",
                    "demographics": {},
                    "clinical_events": [],
                    "lab_results": [],
                }
            ]
        )
        self.assertEqual(len(df), 1)

    def test_no_diagnosis(self):
        df = self.etl.transform(
            [
                {
                    "patient_id": "X",
                    "demographics": {},
                    "clinical_events": [
                        {"type": "procedure", "code": "ABC", "date": "2023-01-01"}
                    ],
                    "lab_results": [],
                }
            ]
        )
        self.assertEqual(len(df), 1)

    def test_load_creates_file(self):
        df = pd.DataFrame({"patient_id": ["P001"], "age": [45]})
        out = os.path.join(self.tmp, "f.parquet")
        self.assertTrue(os.path.exists(self.etl.load(df, output_path=out)))

    def test_load_returns_path(self):
        df = pd.DataFrame({"patient_id": ["P001"]})
        self.assertIsNotNone(
            self.etl.load(df, output_path=os.path.join(self.tmp, "o.parquet"))
        )


# ─────────────────────────────────────────────────────────────────────────────
class TestClinicalMetrics(unittest.TestCase):
    def setUp(self):
        from monitoring.clinical_metrics import ClinicalMetrics

        self.m = ClinicalMetrics()

    def test_patient_keys(self):
        r = self.m.calculate_mock_patient_metrics("P1")
        for k in [
            "readmission_risk_7d",
            "mortality_risk_30d",
            "length_of_stay_prediction",
            "medication_adherence_score",
        ]:
            self.assertIn(k, r)

    def test_ranges(self):
        r = self.m.calculate_mock_patient_metrics("P2")
        self.assertGreaterEqual(r["readmission_risk_7d"], 0)
        self.assertLessEqual(r["readmission_risk_7d"], 1)

    def test_deterministic(self):
        self.assertEqual(
            self.m.calculate_mock_patient_metrics("X")["readmission_risk_7d"],
            self.m.calculate_mock_patient_metrics("X")["readmission_risk_7d"],
        )

    def test_cohort(self):
        r = self.m.calculate_cohort_metrics("c")
        self.assertIn("cohort_size", r)
        self.assertIn("model_accuracy", r)


# ─────────────────────────────────────────────────────────────────────────────
class TestConceptDrift(unittest.TestCase):
    def setUp(self):
        from monitoring.concept_drift import ConceptDriftDetector

        self.d = ConceptDriftDetector("m")

    def test_stable_init(self):
        self.assertEqual(self.d.drift_status, "Stable")

    def test_empty(self):
        self.assertEqual(self.d.check_for_drift([])["status"], "Stable")

    def test_result_keys(self):
        r = self.d.check_for_drift([{"age": 55, "prediction": 0.35}])
        self.assertIn("model", r)
        self.assertIn("status", r)
        self.assertIn("last_checked", r)

    def test_stable_normal_data(self):
        from monitoring.concept_drift import ConceptDriftDetector

        d = ConceptDriftDetector("m", sensitivity=0.5)
        r = d.check_for_drift([{"age": 55, "prediction": 0.35}] * 20)
        self.assertIn("status", r)


# ─────────────────────────────────────────────────────────────────────────────
class TestAdverseEventReporter(unittest.TestCase):
    def setUp(self):
        from monitoring.adverse_event_reporting import AdverseEventReporter

        self.r = AdverseEventReporter()

    def test_returns_id(self):
        self.assertIsInstance(self.r.report_event("P", {"type": "fall"}), str)

    def test_stores(self):
        self.r.report_event("P", {"type": "fall"})
        self.assertEqual(len(self.r.event_log), 1)

    def test_status_reported(self):
        self.r.report_event("P", {"type": "x"})
        self.assertEqual(self.r.event_log[0]["status"], "Reported")

    def test_default_limit(self):
        for i in range(15):
            self.r.report_event(f"P{i}", {"type": "x"})
        self.assertEqual(len(self.r.get_recent_events()), 10)

    def test_custom_limit(self):
        for i in range(8):
            self.r.report_event(f"P{i}", {"type": "x"})
        self.assertEqual(len(self.r.get_recent_events(limit=3)), 3)

    def test_unique_ids(self):
        ids = {self.r.report_event(f"P{i}", {"type": "x"}) for i in range(10)}
        self.assertEqual(len(ids), 10)

    def test_details_preserved(self):
        self.r.report_event("P", {"type": "med", "severity": "crit", "score": 0.9})
        ev = self.r.event_log[0]
        self.assertEqual(ev["type"], "med")
        self.assertEqual(ev["score"], 0.9)

    def test_empty(self):
        self.assertEqual(self.r.get_recent_events(), [])


# ─────────────────────────────────────────────────────────────────────────────
class TestHealthcareMetrics(unittest.TestCase):
    def setUp(self):
        from utils.healthcare_metrics import HealthcareMetrics

        self.m = HealthcareMetrics()
        self.df = pd.DataFrame(
            {
                "patient_id": ["P001", "P001", "P002", "P003"],
                "encounter_id": ["E001", "E002", "E003", "E004"],
                "admission_date": pd.to_datetime(
                    ["2023-01-01", "2023-02-10", "2023-03-01", "2023-04-01"]
                ),
                "discharge_date": pd.to_datetime(
                    ["2023-01-05", "2023-02-15", "2023-03-08", "2023-04-10"]
                ),
                "mortality": [0, 0, 0, 1],
                "expected": [0.05, 0.08, 0.10, 0.80],
                "readmission": [0, 1, 0, 0],
                "complication": [0, 1, 0, 0],
                "prediction": [0.3, 0.7, 0.2, 0.9],
            }
        )

    def test_los(self):
        los = self.m.calculate_length_of_stay(self.df)
        self.assertEqual(len(los), len(self.df))
        self.assertTrue((los >= 0).all())

    def test_los_first_val(self):
        self.assertAlmostEqual(
            self.m.calculate_length_of_stay(self.df).iloc[0], 4.0, places=1
        )

    def test_los_missing_raises(self):
        with self.assertRaises(ValueError):
            self.m.calculate_length_of_stay(self.df.drop(columns=["admission_date"]))

    def test_readmission_rate(self):
        r = self.m.calculate_readmission_rate(self.df, 30)
        self.assertGreaterEqual(r, 0)
        self.assertLessEqual(r, 1)

    def test_mortality_index(self):
        self.assertIsInstance(self.m.calculate_mortality_index(self.df), float)

    def test_mortality_missing_raises(self):
        with self.assertRaises(ValueError):
            self.m.calculate_mortality_index(self.df.drop(columns=["expected"]))

    def test_complication_rate(self):
        r = self.m.calculate_complication_rate(self.df)
        self.assertGreaterEqual(r, 0)
        self.assertLessEqual(r, 1)

    def test_evaluate(self):
        r = self.m.evaluate_clinical_model(self.df, "mortality", "prediction")
        self.assertIn("auc", r)
        self.assertIn("brier_score", r)

    def test_evaluate_bad_col(self):
        with self.assertRaises(ValueError):
            self.m.evaluate_clinical_model(self.df, "ghost", "prediction")

    def test_oe_ratio(self):
        r = self.m.calculate_observed_expected_ratio(self.df, "mortality", "expected")
        self.assertIsInstance(r, float)
        self.assertGreaterEqual(r, 0)

    def test_excess_events(self):
        self.assertIsInstance(
            self.m.calculate_excess_events(self.df, "mortality", "expected"),
            (int, float),
        )

    def test_smr(self):
        self.assertIn("smr", self.m.calculate_standardized_mortality_ratio(self.df))

    def test_quality_metrics(self):
        self.assertIn("mean_los", self.m.calculate_quality_metrics(self.df))


# ─────────────────────────────────────────────────────────────────────────────
class TestSyntheticData(unittest.TestCase):
    def test_generate_records(self):
        from data.synthetic_clinical_data import ClinicalDataGenerator

        records = ClinicalDataGenerator(seed=42).generate_patient_records(n=20)
        if isinstance(records, pd.DataFrame):
            self.assertEqual(len(records), 20)
        else:
            self.assertEqual(len(records), 20)

    def test_record_structure(self):
        from data.synthetic_clinical_data import ClinicalDataGenerator

        records = ClinicalDataGenerator(seed=0).generate_patient_records(n=5)
        if isinstance(records, pd.DataFrame):
            self.assertIn("patient_id", records.columns)
        else:
            [self.assertIn("patient_id", r) for r in records]

    def test_seed_reproducibility(self):
        from data.synthetic_clinical_data import ClinicalDataGenerator

        r1 = ClinicalDataGenerator(seed=7).generate_patient_records(n=10)
        r2 = ClinicalDataGenerator(seed=7).generate_patient_records(n=10)
        if isinstance(r1, pd.DataFrame):
            self.assertEqual(r1.iloc[0]["patient_id"], r2.iloc[0]["patient_id"])
        else:
            self.assertEqual(r1[0]["patient_id"], r2[0]["patient_id"])


# ─────────────────────────────────────────────────────────────────────────────
class TestFHIRConnector(unittest.TestCase):
    def test_trailing_slash(self):
        from utils.fhir_connector import FHIRConnector

        self.assertTrue(FHIRConnector("http://test").base_url.endswith("/"))

    def test_already_slash(self):
        from utils.fhir_connector import FHIRConnector

        c = FHIRConnector("http://test/")
        self.assertEqual(c.base_url.count("//"), 1)

    def test_unreachable_raises(self):
        from utils.fhir_connector import FHIRConnector

        c = FHIRConnector(
            "http://localhost:19999", timeout=1, max_retries=1, retry_delay=0
        )
        with self.assertRaises(Exception):
            c.get_patient_data("P001")


# ─────────────────────────────────────────────────────────────────────────────
try:
    from fastapi.testclient import TestClient
    from serving.rest_api import app

    _API_OK = app is not None
except ImportError:
    _API_OK = False


@unittest.skipUnless(_API_OK, "fastapi/httpx not installed")
class TestRestAPI(unittest.TestCase):
    def setUp(self):
        self.c = TestClient(app)

    def test_health(self):
        r = self.c.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "healthy")

    def test_list_models(self):
        r = self.c.get("/models")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.json()["models"]), 0)

    def test_predict(self):
        r = self.c.post(
            "/predict",
            json={
                "model_name": "transformer_model",
                "patient_data": {
                    "patient_id": "P1",
                    "demographics": {},
                    "clinical_events": [],
                },
            },
        )
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn("request_id", d)
        self.assertIn("predictions", d)
        self.assertIn("uncertainty", d)

    def test_predict_invalid(self):
        r = self.c.post(
            "/predict", json={"model_name": "transformer_model", "patient_data": {}}
        )
        self.assertEqual(r.status_code, 422)

    def test_predict_unknown_model(self):
        r = self.c.post(
            "/predict",
            json={
                "model_name": "ghost_xyz",
                "patient_data": {
                    "patient_id": "P",
                    "demographics": {},
                    "clinical_events": [],
                },
            },
        )
        self.assertEqual(r.status_code, 500)

    def test_metrics(self):
        r = self.c.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_audit_history(self):
        self.c.post(
            "/predict",
            json={
                "model_name": "transformer_model",
                "patient_data": {
                    "patient_id": "AUDIT_X",
                    "demographics": {},
                    "clinical_events": [],
                },
            },
        )
        r = self.c.get("/audit/patient/AUDIT_X")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json()["access_history"], list)

    def test_fhir_unreachable(self):
        r = self.c.post("/fhir/patient/P001/predict?model_name=transformer_model")
        self.assertEqual(r.status_code, 500)

    def test_request_id_header(self):
        r = self.c.get("/health", headers={"X-Request-ID": "test-999"})
        self.assertEqual(r.status_code, 200)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestPHIAuditLogger,
        TestModelRegistry,
        TestTransformerModel,
        TestDeepFMModel,
        TestSurvivalModel,
        TestModelCalibrator,
        TestFairnessEvaluator,
        TestDataValidator,
        TestClinicalETL,
        TestClinicalMetrics,
        TestConceptDrift,
        TestAdverseEventReporter,
        TestHealthcareMetrics,
        TestSyntheticData,
        TestFHIRConnector,
        TestRestAPI,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    result = unittest.TextTestRunner(verbosity=2, failfast=False).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
