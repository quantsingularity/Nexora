"""
PHI Detection module for identifying Protected Health Information.

This module provides utilities for detecting PHI in clinical data
to ensure proper handling and de-identification.
"""

import re
from typing import Any, Dict, List, Optional, Set, Union

import pandas as pd


class PHIDetector:
    """
    Detects Protected Health Information (PHI) in clinical data.

    This class implements detection for the 18 identifiers specified in the
    HIPAA Safe Harbor method, helping to identify PHI before de-identification.
    """

    def __init__(self):
        """Initialize the PHI detector."""
        # Compile regex patterns for various PHI types
        self.patterns = {
            "name": re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),
            "ssn": re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
            "phone": re.compile(
                r"\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"
            ),
            "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
            "address": re.compile(
                r"\b\d+\s+[A-Za-z\s]+,\s+[A-Za-z\s]+,\s+[A-Z]{2}\s+\d{5}(-\d{4})?\b"
            ),
            "date": re.compile(
                r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"
            ),
            "mrn": re.compile(
                r"\b(MRN|mrn|Medical Record Number|medical record number)[:# ]?\s*\d+\b"
            ),
            "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
            "url": re.compile(r'\bhttps?://[^\s<>"]+|www\.[^\s<>"]+\b'),
            "zipcode": re.compile(r"\b\d{5}(-\d{4})?\b"),
        }

    def detect_phi_in_text(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PHI in a text string.

        Args:
            text: Text string to analyze

        Returns:
            Dictionary mapping PHI types to lists of detected instances
        """
        if not text or not isinstance(text, str):
            return {}

        results = {}

        # Apply each pattern
        for phi_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                results[phi_type] = matches

        return results

    def detect_phi_in_dataframe(
        self, df: pd.DataFrame, sample_size: int = 100
    ) -> Dict[str, Dict[str, int]]:
        """
        Detect PHI in a pandas DataFrame.

        Args:
            df: DataFrame to analyze
            sample_size: Number of rows to sample for detection

        Returns:
            Dictionary mapping column names to PHI types and counts
        """
        # Sample rows to reduce processing time
        if len(df) > sample_size:
            sample_df = df.sample(sample_size)
        else:
            sample_df = df

        results = {}

        # Check each column
        for col in sample_df.columns:
            col_results = {}

            # Skip non-string columns
            if not pd.api.types.is_string_dtype(
                sample_df[col]
            ) and not pd.api.types.is_object_dtype(sample_df[col]):
                continue

            # Convert column to string and concatenate values
            text_values = sample_df[col].astype(str).dropna().tolist()

            # Skip empty columns
            if not text_values:
                continue

            # Check each value in the column
            for value in text_values:
                phi_detected = self.detect_phi_in_text(value)

                # Update counts
                for phi_type, instances in phi_detected.items():
                    if phi_type in col_results:
                        col_results[phi_type] += len(instances)
                    else:
                        col_results[phi_type] = len(instances)

            # Only include columns with detected PHI
            if col_results:
                results[col] = col_results

        return results

    def identify_phi_columns(
        self, df: pd.DataFrame, threshold: float = 0.1
    ) -> Dict[str, Set[str]]:
        """
        Identify columns likely to contain PHI.

        Args:
            df: DataFrame to analyze
            threshold: Minimum fraction of rows that must contain PHI

        Returns:
            Dictionary mapping column names to sets of detected PHI types
        """
        # Detect PHI in the DataFrame
        detection_results = self.detect_phi_in_dataframe(df)

        # Calculate sample size
        sample_size = min(len(df), 100)

        # Identify columns with PHI above threshold
        phi_columns = {}
        for col, phi_types in detection_results.items():
            col_phi_types = set()

            for phi_type, count in phi_types.items():
                # Check if PHI appears in enough rows
                if count / sample_size >= threshold:
                    col_phi_types.add(phi_type)

            if col_phi_types:
                phi_columns[col] = col_phi_types

        return phi_columns

    def generate_phi_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a comprehensive PHI detection report.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary containing PHI detection report
        """
        # Identify PHI columns
        phi_columns = self.identify_phi_columns(df)

        # Check column names for PHI indicators
        name_indicators = {
            "name": ["name", "first", "last", "middle"],
            "address": ["address", "street", "city", "state", "zip", "postal"],
            "date": ["date", "dob", "birth", "admission", "discharge"],
            "id": ["id", "identifier", "mrn", "ssn", "social", "account"],
            "contact": ["phone", "email", "fax", "contact", "mobile", "cell"],
        }

        name_based_phi = {}
        for col in df.columns:
            col_lower = col.lower()
            for phi_type, indicators in name_indicators.items():
                if any(indicator in col_lower for indicator in indicators):
                    if col not in name_based_phi:
                        name_based_phi[col] = set()
                    name_based_phi[col].add(phi_type)

        # Combine content-based and name-based detection
        all_phi_columns = set(phi_columns.keys()) | set(name_based_phi.keys())

        combined_results = {}
        for col in all_phi_columns:
            combined_results[col] = {
                "content_detection": phi_columns.get(col, set()),
                "name_indicators": name_based_phi.get(col, set()),
                "risk_level": (
                    "high"
                    if col in phi_columns
                    else "medium" if col in name_based_phi else "low"
                ),
            }

        # Generate summary
        summary = {
            "total_columns": len(df.columns),
            "phi_columns": len(combined_results),
            "high_risk_columns": sum(
                1 for info in combined_results.values() if info["risk_level"] == "high"
            ),
            "medium_risk_columns": sum(
                1
                for info in combined_results.values()
                if info["risk_level"] == "medium"
            ),
            "phi_types_detected": set().union(
                *[
                    info["content_detection"]
                    for info in combined_results.values()
                    if info["content_detection"]
                ]
            ),
        }

        return {"summary": summary, "column_details": combined_results}
