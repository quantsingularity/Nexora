"""
Data Validation Module for Nexora
"""

import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)
ICD10_PATTERN = re.compile(r"^[A-Z][0-9]{2}(\.[0-9]{1,4})?$")


class DataValidator:

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
                    if "max" in rules and num > rules["max"]:
                        errors.append(
                            f"Column '{col}' value {num} at row {idx} exceeds max {rules['max']}."
                        )
                elif dtype == "category":
                    cats = rules.get("categories", [])
                    if val not in cats:
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} not in {cats}."
                        )
                elif dtype == "string":
                    pattern = rules.get("pattern")
                    if pattern and not re.match(pattern, str(val)):
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} does not match pattern."
                        )
                elif dtype == "boolean":
                    if val not in (0, 1, True, False, "true", "false", "True", "False"):
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} is not a boolean."
                        )
                elif dtype == "datetime":
                    try:
                        pd.to_datetime(val)
                    except (ValueError, TypeError):
                        errors.append(
                            f"Column '{col}' value '{val}' at row {idx} is not a valid datetime."
                        )
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_relationships(
        self, df: pd.DataFrame, relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        errors: List[str] = []
        for rel in relationships:
            rel_type = rel.get("type", "")
            if rel_type == "temporal":
                fc, sc = rel["first"], rel["second"]
                relation = rel.get("relation", "<=")
                if fc not in df.columns or sc not in df.columns:
                    errors.append(f"Temporal columns '{fc}'/'{sc}' not found.")
                    continue
                fv = pd.to_datetime(df[fc])
                sv = pd.to_datetime(df[sc])
                if relation == "<=":
                    bad = df[fv > sv]
                elif relation == "<":
                    bad = df[fv >= sv]
                elif relation == ">=":
                    bad = df[fv < sv]
                else:
                    bad = pd.DataFrame()
                if len(bad) > 0:
                    errors.append(
                        f"Temporal '{fc}' {relation} '{sc}' fails for {len(bad)} rows."
                    )
            elif rel_type == "logical":
                cond, impl = rel["condition"], rel["implication"]
                try:
                    cm = df.eval(cond)
                    im = df.eval(impl)
                    viol = cm & ~im
                    if viol.any():
                        errors.append(
                            f"Logical '{cond}' => '{impl}' fails for {viol.sum()} rows."
                        )
                except Exception as e:
                    errors.append(f"Failed to evaluate logical relationship: {e}")
            elif rel_type == "referential":
                src, tgt = rel["source"], rel["target"]
                if src not in df.columns or tgt not in df.columns:
                    errors.append(f"Referential columns '{src}'/'{tgt}' not found.")
                    continue
                missing = ~df[src].isin(df[tgt])
                if missing.any():
                    errors.append(
                        f"Referential integrity: {missing.sum()} values in '{src}' not in '{tgt}'."
                    )
        return {"valid": len(errors) == 0, "errors": errors}

    def detect_outliers(
        self,
        df: pd.DataFrame,
        columns: List[str],
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> Dict[str, Any]:
        outliers: Dict[str, List] = {}
        for col in columns:
            if col not in df.columns:
                continue
            series = pd.to_numeric(df[col], errors="coerce")
            clean = series.dropna()
            if clean.empty:
                outliers[col] = []
                continue
            if method == "iqr":
                q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
                iqr = q3 - q1
                mask = (series < q1 - threshold * iqr) | (series > q3 + threshold * iqr)
            elif method == "z-score":
                mean, std = clean.mean(), clean.std()
                if std == 0:
                    outliers[col] = []
                    continue
                mask = ((series - mean).abs() / std) > threshold
            else:
                raise ValueError(f"Unknown outlier method: {method}")
            outliers[col] = list(df.index[mask & series.notna()])
        return {
            "outliers": outliers,
            "total_outliers": sum(len(v) for v in outliers.values()),
        }

    def check_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        mc = df.isnull().sum().to_dict()
        mp = (df.isnull().mean() * 100).round(2).to_dict()
        total = int(df.isnull().sum().sum())
        return {
            "missing_counts": mc,
            "missing_percentage": mp,
            "total_missing": total,
            "has_missing": total > 0,
        }

    def validate_icd10_codes(self, codes: pd.Series) -> Dict[str, Any]:
        invalid = [
            str(c) for c in codes if not pd.isna(c) and not ICD10_PATTERN.match(str(c))
        ]
        return {
            "valid": len(invalid) == 0,
            "invalid_codes": invalid,
            "total_checked": len(codes),
            "invalid_count": len(invalid),
        }

    def validate_date_ranges(
        self,
        df: pd.DataFrame,
        date_column: str,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        if date_column not in df.columns:
            return {
                "valid": False,
                "out_of_range": [],
                "error": f"Column '{date_column}' not found.",
            }
        dates = pd.to_datetime(df[date_column], errors="coerce")
        out_of_range = []
        for idx, d in dates.items():
            if pd.isna(d):
                continue
            if min_date and d < pd.to_datetime(min_date):
                out_of_range.append(int(idx))
            elif max_date and d > pd.to_datetime(max_date):
                out_of_range.append(int(idx))
        return {
            "valid": len(out_of_range) == 0,
            "out_of_range": out_of_range,
            "total_checked": int(dates.notna().sum()),
        }

    def check_duplicates(
        self, df: pd.DataFrame, subset: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        mask = df.duplicated(subset=subset, keep=False)
        return {
            "has_duplicates": bool(mask.any()),
            "duplicate_count": int(mask.sum()),
            "duplicate_indices": list(df.index[mask]),
        }

    def validate_consistency(
        self, df: pd.DataFrame, rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        rule_results: Dict[str, Any] = {}
        all_valid = True
        for rule in rules:
            name = rule.get("name", "unnamed_rule")
            condition, expected = rule["condition"], rule["expected"]
            try:
                cm = df.eval(condition)
                em = df.eval(expected)
                if not cm.any():
                    rule_results[name] = {
                        "valid": True,
                        "violations": 0,
                        "note": "No rows matched condition.",
                    }
                    continue
                viol = int((cm & ~em).sum())
                valid = viol == 0
                if not valid:
                    all_valid = False
                rule_results[name] = {
                    "valid": valid,
                    "violations": viol,
                    "condition": condition,
                    "expected": expected,
                }
            except Exception as e:
                all_valid = False
                rule_results[name] = {"valid": False, "error": str(e)}
        return {"valid": all_valid, "rule_results": rule_results}

    def generate_validation_report(
        self,
        df: pd.DataFrame,
        schema: Optional[Dict[str, Any]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        outlier_columns: Optional[List[str]] = None,
        consistency_rules: Optional[List[Dict[str, Any]]] = None,
        icd10_column: Optional[str] = None,
        date_columns: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        error_count = 0
        warning_count = 0

        sv = (
            self.validate_schema(df, schema)
            if schema
            else {"valid": True, "errors": []}
        )
        report["schema_validation"] = sv
        if not sv["valid"]:
            error_count += len(sv["errors"])

        rv = (
            self.validate_relationships(df, relationships)
            if relationships
            else {"valid": True, "errors": []}
        )
        report["relationship_validation"] = rv
        if not rv["valid"]:
            error_count += len(rv["errors"])

        mv = self.check_missing_values(df)
        report["missing_values"] = mv
        if mv["has_missing"]:
            warning_count += 1

        od = (
            self.detect_outliers(df, outlier_columns)
            if outlier_columns
            else {"outliers": {}, "total_outliers": 0}
        )
        report["outliers"] = od
        if od["total_outliers"] > 0:
            warning_count += od["total_outliers"]

        dup = self.check_duplicates(df)
        report["duplicates"] = dup
        if dup["has_duplicates"]:
            warning_count += 1

        cr = (
            self.validate_consistency(df, consistency_rules)
            if consistency_rules
            else {"valid": True, "rule_results": {}}
        )
        report["consistency"] = cr
        if not cr["valid"]:
            error_count += sum(
                1 for r in cr["rule_results"].values() if not r.get("valid", True)
            )

        if icd10_column and icd10_column in df.columns:
            report["icd10_validation"] = self.validate_icd10_codes(df[icd10_column])
        else:
            report["icd10_validation"] = {"valid": True, "invalid_codes": []}

        report["summary"] = {
            "valid": error_count == 0,
            "error_count": error_count,
            "warning_count": warning_count,
            "row_count": len(df),
            "column_count": len(df.columns),
        }
        return report
