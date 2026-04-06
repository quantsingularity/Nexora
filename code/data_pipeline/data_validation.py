"""
Data Validation Module for Nexora

Provides schema validation, relationship checking, outlier detection,
and comprehensive reporting for clinical DataFrames.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

ICD10_PATTERN = re.compile(r"^[A-Z][0-9]{2}(\.[0-9]{1,4})?$")


class DataValidator:
    """Validates clinical DataFrames against schemas, relationships, and quality rules."""

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def validate_schema(
        self, df: pd.DataFrame, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        errors: List[str] = []

        for col, rules in schema.items():
            required = rules.get("required", False)
            if col not in df.columns:
                if required:
                    errors.append(f"Required column '{col}' is missing.")
                continue

            series = df[col]

            if rules.get("unique") and series.duplicated().any():
                errors.append(f"Column '{col}' contains duplicate values.")

            dtype = rules.get("type", "")
            for idx, val in series.items():
                if pd.isna(val):
                    if required:
                        errors.append(f"Column '{col}' has a null value at row {idx}.")
                    continue

                if dtype == "integer":
                    try:
                        num = float(val)
                        if num != int(num):
                            raise ValueError
                    except (ValueError, TypeError):
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} is not an integer."
                        )
                        continue
                    num = float(val)
                    if "min" in rules and num < rules["min"]:
                        errors.append(
                            f"Column '{col}' value {val} at row {idx} is below min {rules['min']}."
                        )
                    if "max" in rules and num > rules["max"]:
                        errors.append(
                            f"Column '{col}' value {val} at row {idx} exceeds max {rules['max']}."
                        )

                elif dtype == "float":
                    try:
                        num = float(val)
                    except (ValueError, TypeError):
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} is not a float."
                        )
                        continue
                    if "min" in rules and num < rules["min"]:
                        errors.append(
                            f"Column '{col}' value {num} at row {idx} is below min {rules['min']}."
                        )

                elif dtype == "category":
                    categories = rules.get("categories", [])
                    if val not in categories:
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} not in {categories}."
                        )

                elif dtype == "string":
                    pattern = rules.get("pattern")
                    if pattern and not re.match(pattern, str(val)):
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} does not match pattern."
                        )

                elif dtype == "datetime":
                    try:
                        pd.to_datetime(val)
                    except Exception:
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} is not a valid datetime."
                        )

        return {"valid": len(errors) == 0, "errors": errors}

    # ------------------------------------------------------------------
    # Relationship validation
    # ------------------------------------------------------------------

    def validate_relationships(
        self, df: pd.DataFrame, relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        errors: List[str] = []

        for rel in relationships:
            rel_type = rel.get("type", "")

            if rel_type == "temporal":
                first_col = rel["first"]
                second_col = rel["second"]
                relation = rel.get("relation", "<=")
                first_vals = pd.to_datetime(df[first_col])
                second_vals = pd.to_datetime(df[second_col])
                if relation == "<=":
                    violations = first_vals > second_vals
                elif relation == "<":
                    violations = first_vals >= second_vals
                elif relation == ">=":
                    violations = first_vals < second_vals
                else:
                    violations = pd.Series([False] * len(df))
                if violations.any():
                    errors.append(
                        f"Temporal relationship violated: '{first_col}' {relation} '{second_col}' "
                        f"fails at rows {df.index[violations].tolist()}."
                    )

            elif rel_type == "logical":
                condition = rel["condition"]
                implication = rel["implication"]
                try:
                    cond_mask = df.eval(condition)
                    impl_mask = df.eval(implication)
                    violations = cond_mask & ~impl_mask
                    if violations.any():
                        errors.append(
                            f"Logical relationship violated: when '{condition}', '{implication}' "
                            f"must hold. Fails at rows {df.index[violations].tolist()}."
                        )
                except Exception as exc:
                    errors.append(f"Error evaluating logical relationship: {exc}")

        return {"valid": len(errors) == 0, "errors": errors}

    # ------------------------------------------------------------------
    # Outlier detection
    # ------------------------------------------------------------------

    def detect_outliers(
        self,
        df: pd.DataFrame,
        columns: List[str],
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> Dict[str, Any]:
        outliers: Dict[str, List[int]] = {}

        for col in columns:
            if col not in df.columns:
                continue
            series = pd.to_numeric(df[col], errors="coerce").dropna()

            if method == "iqr":
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
                out_idx = df.index[
                    pd.to_numeric(df[col], errors="coerce").lt(lower)
                    | pd.to_numeric(df[col], errors="coerce").gt(upper)
                ].tolist()
            elif method == "z-score":
                mean = series.mean()
                std = series.std()
                if std == 0:
                    out_idx = []
                else:
                    z = (pd.to_numeric(df[col], errors="coerce") - mean) / std
                    out_idx = df.index[z.abs() > threshold].tolist()
            else:
                out_idx = []

            outliers[col] = out_idx

        return {"outliers": outliers, "method": method, "threshold": threshold}

    # ------------------------------------------------------------------
    # Missing value check
    # ------------------------------------------------------------------

    def check_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        missing_counts = df.isnull().sum().to_dict()
        missing_pct = (df.isnull().mean() * 100).to_dict()
        return {
            "missing_counts": missing_counts,
            "missing_percentage": missing_pct,
            "total_missing": int(df.isnull().sum().sum()),
        }

    # ------------------------------------------------------------------
    # ICD-10 validation
    # ------------------------------------------------------------------

    def validate_icd10_codes(self, series: pd.Series) -> Dict[str, Any]:
        invalid: List[str] = []
        for code in series.dropna():
            if not ICD10_PATTERN.match(str(code)):
                invalid.append(str(code))
        return {"valid": len(invalid) == 0, "invalid_codes": invalid}

    # ------------------------------------------------------------------
    # Date range validation
    # ------------------------------------------------------------------

    def validate_date_ranges(
        self,
        df: pd.DataFrame,
        date_column: str,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        dates = pd.to_datetime(df[date_column])
        out_of_range: List[int] = []

        min_ts = pd.to_datetime(min_date) if min_date else None
        max_ts = pd.to_datetime(max_date) if max_date else None

        for idx, val in dates.items():
            if pd.isna(val):
                continue
            if min_ts is not None and val < min_ts:
                out_of_range.append(idx)
            elif max_ts is not None and val > max_ts:
                out_of_range.append(idx)

        return {"valid": len(out_of_range) == 0, "out_of_range": out_of_range}

    # ------------------------------------------------------------------
    # Duplicate check
    # ------------------------------------------------------------------

    def check_duplicates(
        self, df: pd.DataFrame, subset: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        dup_mask = df.duplicated(subset=subset, keep=False)
        dup_indices = df.index[dup_mask].tolist()
        return {
            "has_duplicates": dup_mask.any(),
            "duplicate_indices": dup_indices,
            "duplicate_count": int(dup_mask.sum()),
        }

    # ------------------------------------------------------------------
    # Consistency validation
    # ------------------------------------------------------------------

    def validate_consistency(
        self, df: pd.DataFrame, rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        rule_results: Dict[str, Any] = {}

        for rule in rules:
            name = rule.get("name", "unnamed")
            condition = rule["condition"]
            expected = rule["expected"]
            try:
                cond_mask = df.eval(condition)
                exp_mask = df.eval(expected)
                violations = cond_mask & ~exp_mask
                valid = not violations.any()
                rule_results[name] = {
                    "valid": valid,
                    "violations": int(violations.sum()),
                    "violation_indices": df.index[violations].tolist(),
                }
            except Exception as exc:
                rule_results[name] = {"valid": False, "error": str(exc)}

        overall_valid = all(r.get("valid", False) for r in rule_results.values())
        return {"valid": overall_valid, "rule_results": rule_results}

    # ------------------------------------------------------------------
    # Comprehensive report
    # ------------------------------------------------------------------

    def generate_validation_report(
        self,
        df: pd.DataFrame,
        schema: Optional[Dict[str, Any]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        outlier_columns: Optional[List[str]] = None,
        consistency_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        error_count = 0
        warning_count = 0

        if schema:
            sv = self.validate_schema(df, schema)
            report["schema_validation"] = sv
            if not sv["valid"]:
                error_count += len(sv["errors"])

        if relationships:
            rv = self.validate_relationships(df, relationships)
            report["relationship_validation"] = rv
            if not rv["valid"]:
                error_count += len(rv["errors"])

        mv = self.check_missing_values(df)
        report["missing_values"] = mv
        warning_count += sum(1 for v in mv["missing_counts"].values() if v > 0)

        if outlier_columns:
            ov = self.detect_outliers(df, outlier_columns)
            report["outliers"] = ov
            warning_count += sum(1 for v in ov["outliers"].values() if len(v) > 0)
        else:
            report["outliers"] = {"outliers": {}}

        dup = self.check_duplicates(df)
        report["duplicates"] = dup
        if dup["has_duplicates"]:
            warning_count += 1

        if consistency_rules:
            cv = self.validate_consistency(df, consistency_rules)
            report["consistency"] = cv
            if not cv["valid"]:
                error_count += sum(
                    1 for r in cv["rule_results"].values() if not r.get("valid", True)
                )
        else:
            report["consistency"] = {"valid": True, "rule_results": {}}

        all_valid = error_count == 0
        report["summary"] = {
            "valid": all_valid,
            "error_count": error_count,
            "warning_count": warning_count,
            "total_rows": len(df),
            "total_columns": len(df.columns),
        }

        logger.info(
            f"Validation report: valid={all_valid}, errors={error_count}, warnings={warning_count}"
        )
        return report
