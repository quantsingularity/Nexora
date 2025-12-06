"""
ICD-10 Encoder Module for Nexora

This module provides functionality for encoding and processing ICD-10 diagnosis codes
in healthcare data. It includes utilities for code normalization, grouping, and
feature engineering based on ICD-10 hierarchical structure.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class ICD10Encoder:
    """
    A class for encoding ICD-10 diagnosis codes into features for machine learning models.

    This encoder handles various ICD-10 code formats, normalizes them, and provides
    methods to transform them into categorical or numerical features based on different
    grouping strategies.
    """

    ICD10_CHAPTERS = {
        "A00-B99": "Infectious and parasitic diseases",
        "C00-D49": "Neoplasms",
        "D50-D89": "Blood and immune mechanism disorders",
        "E00-E89": "Endocrine, nutritional and metabolic diseases",
        "F01-F99": "Mental, behavioral and neurodevelopmental disorders",
        "G00-G99": "Nervous system diseases",
        "H00-H59": "Eye and adnexa diseases",
        "H60-H95": "Ear and mastoid process diseases",
        "I00-I99": "Circulatory system diseases",
        "J00-J99": "Respiratory system diseases",
        "K00-K95": "Digestive system diseases",
        "L00-L99": "Skin and subcutaneous tissue diseases",
        "M00-M99": "Musculoskeletal system and connective tissue diseases",
        "N00-N99": "Genitourinary system diseases",
        "O00-O9A": "Pregnancy, childbirth and the puerperium",
        "P00-P96": "Certain conditions originating in the perinatal period",
        "Q00-Q99": "Congenital malformations, deformations and chromosomal abnormalities",
        "R00-R99": "Symptoms, signs and abnormal clinical and laboratory findings",
        "S00-T88": "Injury, poisoning and certain other consequences of external causes",
        "V00-Y99": "External causes of morbidity",
        "Z00-Z99": "Factors influencing health status and contact with health services",
    }
    CHRONIC_CONDITION_GROUPS = {
        "hypertension": ["I10", "I11", "I12", "I13", "I15"],
        "diabetes": ["E08", "E09", "E10", "E11", "E13"],
        "copd": ["J40", "J41", "J42", "J43", "J44"],
        "asthma": ["J45"],
        "heart_failure": ["I50"],
        "ischemic_heart": ["I20", "I21", "I22", "I23", "I24", "I25"],
        "kidney_disease": ["N18"],
        "liver_disease": ["K70", "K71", "K72", "K73", "K74", "K75", "K76", "K77"],
        "cancer": [
            "C00",
            "C01",
            "C02",
            "C03",
            "C04",
            "C05",
            "C06",
            "C07",
            "C08",
            "C09",
            "C10",
            "C11",
            "C12",
            "C13",
            "C14",
            "C15",
            "C16",
            "C17",
            "C18",
            "C19",
            "C20",
            "C21",
            "C22",
            "C23",
            "C24",
            "C25",
            "C26",
            "C30",
            "C31",
            "C32",
            "C33",
            "C34",
            "C37",
            "C38",
            "C39",
            "C40",
            "C41",
            "C43",
            "C44",
            "C45",
            "C46",
            "C47",
            "C48",
            "C49",
            "C50",
            "C51",
            "C52",
            "C53",
            "C54",
            "C55",
            "C56",
            "C57",
            "C58",
            "C60",
            "C61",
            "C62",
            "C63",
            "C64",
            "C65",
            "C66",
            "C67",
            "C68",
            "C69",
            "C70",
            "C71",
            "C72",
            "C73",
            "C74",
            "C75",
            "C76",
            "C81",
            "C82",
            "C83",
            "C84",
            "C85",
            "C86",
            "C88",
            "C90",
            "C91",
            "C92",
            "C93",
            "C94",
            "C95",
            "D00",
            "D01",
            "D02",
            "D03",
            "D04",
            "D05",
            "D06",
            "D07",
            "D09",
        ],
        "depression": ["F32", "F33"],
        "dementia": ["F01", "F02", "F03", "G30"],
        "stroke": ["I60", "I61", "I62", "I63", "I65", "I66", "I67", "I69"],
        "obesity": ["E66"],
        "substance_abuse": [
            "F10",
            "F11",
            "F12",
            "F13",
            "F14",
            "F15",
            "F16",
            "F17",
            "F18",
            "F19",
        ],
    }

    def __init__(
        self,
        normalize_codes: bool = True,
        include_dot: bool = False,
        max_code_length: Optional[int] = None,
        custom_code_groups: Optional[Dict[str, List[str]]] = None,
    ) -> Any:
        """
        Initialize the ICD-10 encoder.

        Args:
            normalize_codes: Whether to normalize ICD-10 codes (remove dots, uppercase)
            include_dot: Whether to include dots in normalized codes
            max_code_length: Maximum length to truncate codes to (e.g., 3 for category level)
            custom_code_groups: Custom groupings of ICD-10 codes for feature engineering
        """
        self.normalize_codes = normalize_codes
        self.include_dot = include_dot
        self.max_code_length = max_code_length
        self.custom_code_groups = custom_code_groups or {}
        self.code_groups = {**self.CHRONIC_CONDITION_GROUPS, **self.custom_code_groups}
        self.chapter_lookup = self._build_chapter_lookup()
        logger.info(
            f"Initialized ICD10Encoder with {len(self.code_groups)} code groups"
        )

    def _build_chapter_lookup(self) -> Dict[str, str]:
        """
        Build a lookup dictionary to map ICD-10 codes to their respective chapters.

        Returns:
            Dictionary mapping code prefixes to chapter names
        """
        chapter_lookup = {}
        for chapter_range, chapter_name in self.ICD10_CHAPTERS.items():
            start, end = chapter_range.split("-")
            if end.endswith("A"):
                end = end[:-1] + "Z"
            start_letter, start_num = (start[0], int(start[1:]))
            end_letter, end_num = (end[0], int(end[1:]))
            current_letter = start_letter
            while ord(current_letter) <= ord(end_letter):
                if current_letter == start_letter and current_letter == end_letter:
                    for num in range(start_num, end_num + 1):
                        code_prefix = f"{current_letter}{num:02d}"
                        chapter_lookup[code_prefix] = chapter_name
                elif current_letter == start_letter:
                    for num in range(start_num, 100):
                        code_prefix = f"{current_letter}{num:02d}"
                        chapter_lookup[code_prefix] = chapter_name
                elif current_letter == end_letter:
                    for num in range(0, end_num + 1):
                        code_prefix = f"{current_letter}{num:02d}"
                        chapter_lookup[code_prefix] = chapter_name
                else:
                    for num in range(0, 100):
                        code_prefix = f"{current_letter}{num:02d}"
                        chapter_lookup[code_prefix] = chapter_name
                current_letter = chr(ord(current_letter) + 1)
        return chapter_lookup

    def normalize_icd10(self, code: str) -> str:
        """
        Normalize an ICD-10 code by standardizing format.

        Args:
            code: The ICD-10 code to normalize

        Returns:
            Normalized ICD-10 code
        """
        if not code or not isinstance(code, str):
            return ""
        normalized = code.strip().upper()
        if not self.include_dot:
            normalized = normalized.replace(".", "")
        if not re.match("^[A-Z]\\d+(\\.\\d+)?$", normalized):
            logger.warning(f"Invalid ICD-10 code format: {code}")
            return ""
        if self.max_code_length and len(normalized) > self.max_code_length:
            dot_position = normalized.find(".")
            if self.include_dot and 0 < dot_position < self.max_code_length:
                return normalized[: self.max_code_length]
            no_dot = normalized.replace(".", "")
            if len(no_dot) > self.max_code_length:
                result = no_dot[: self.max_code_length]
                if self.include_dot and len(result) >= 4:
                    result = result[:3] + "." + result[3:]
                return result
        return normalized

    def get_chapter(self, code: str) -> Optional[str]:
        """
        Get the ICD-10 chapter for a given code.

        Args:
            code: The ICD-10 code

        Returns:
            Chapter name or None if not found
        """
        if not code or not isinstance(code, str):
            return None
        normalized = self.normalize_icd10(code)
        if not normalized:
            return None
        prefix = normalized[:3] if len(normalized) >= 3 else normalized
        prefix = prefix.replace(".", "")
        if len(prefix) < 3:
            prefix = prefix.ljust(3, "0")
        return self.chapter_lookup.get(prefix)

    def get_code_group(self, code: str) -> List[str]:
        """
        Get all groups that a code belongs to.

        Args:
            code: The ICD-10 code

        Returns:
            List of group names the code belongs to
        """
        if not code or not isinstance(code, str):
            return []
        normalized = self.normalize_icd10(code)
        if not normalized:
            return []
        matching_groups = []
        for group_name, code_list in self.code_groups.items():
            if any((normalized.startswith(self.normalize_icd10(c)) for c in code_list)):
                matching_groups.append(group_name)
        return matching_groups

    def encode_codes_binary(
        self, codes: List[str], level: str = "chapter"
    ) -> Dict[str, int]:
        """
        Encode a list of ICD-10 codes as binary features.

        Args:
            codes: List of ICD-10 codes
            level: Level of encoding ('chapter', 'category', 'group', or 'custom')

        Returns:
            Dictionary with feature names as keys and binary values (0/1)
        """
        if not codes:
            return {}
        features = {}
        if level == "chapter":
            for chapter_range, chapter_name in self.ICD10_CHAPTERS.items():
                feature_name = f"icd10_chapter_{chapter_range}"
                features[feature_name] = 0
            for code in codes:
                chapter = self.get_chapter(code)
                if chapter:
                    for chapter_range, chapter_name in self.ICD10_CHAPTERS.items():
                        if chapter_name == chapter:
                            feature_name = f"icd10_chapter_{chapter_range}"
                            features[feature_name] = 1
                            break
        elif level == "category":
            unique_categories = set()
            for code in codes:
                normalized = self.normalize_icd10(code)
                if normalized:
                    category = normalized[:3] if len(normalized) >= 3 else normalized
                    category = category.replace(".", "")
                    unique_categories.add(category)
            for category in unique_categories:
                feature_name = f"icd10_category_{category}"
                features[feature_name] = 1
        elif level == "group":
            for group_name in self.code_groups.keys():
                feature_name = f"icd10_group_{group_name}"
                features[feature_name] = 0
            for code in codes:
                groups = self.get_code_group(code)
                for group in groups:
                    feature_name = f"icd10_group_{group}"
                    features[feature_name] = 1
        elif level == "custom":
            if not self.custom_code_groups:
                logger.warning(
                    "No custom code groups defined for 'custom' level encoding"
                )
                return {}
            for group_name in self.custom_code_groups.keys():
                feature_name = f"icd10_custom_{group_name}"
                features[feature_name] = 0
            for code in codes:
                normalized = self.normalize_icd10(code)
                if not normalized:
                    continue
                for group_name, code_list in self.custom_code_groups.items():
                    if any(
                        (
                            normalized.startswith(self.normalize_icd10(c))
                            for c in code_list
                        )
                    ):
                        feature_name = f"icd10_custom_{group_name}"
                        features[feature_name] = 1
        else:
            logger.error(f"Unsupported encoding level: {level}")
            return {}
        return features

    def encode_codes_count(
        self, codes: List[str], level: str = "chapter"
    ) -> Dict[str, int]:
        """
        Encode a list of ICD-10 codes as count features.

        Args:
            codes: List of ICD-10 codes
            level: Level of encoding ('chapter', 'category', 'group', or 'custom')

        Returns:
            Dictionary with feature names as keys and count values
        """
        if not codes:
            return {}
        features = {}
        if level == "chapter":
            for chapter_range, _ in self.ICD10_CHAPTERS.items():
                feature_name = f"icd10_chapter_{chapter_range}_count"
                features[feature_name] = 0
            for code in codes:
                chapter = self.get_chapter(code)
                if chapter:
                    for chapter_range, chapter_name in self.ICD10_CHAPTERS.items():
                        if chapter_name == chapter:
                            feature_name = f"icd10_chapter_{chapter_range}_count"
                            features[feature_name] = features.get(feature_name, 0) + 1
                            break
        elif level == "category":
            category_counts = defaultdict(int)
            for code in codes:
                normalized = self.normalize_icd10(code)
                if normalized:
                    category = normalized[:3] if len(normalized) >= 3 else normalized
                    category = category.replace(".", "")
                    category_counts[category] += 1
            for category, count in category_counts.items():
                feature_name = f"icd10_category_{category}_count"
                features[feature_name] = count
        elif level == "group":
            for group_name in self.code_groups.keys():
                feature_name = f"icd10_group_{group_name}_count"
                features[feature_name] = 0
            for code in codes:
                groups = self.get_code_group(code)
                for group in groups:
                    feature_name = f"icd10_group_{group}_count"
                    features[feature_name] = features.get(feature_name, 0) + 1
        elif level == "custom":
            if not self.custom_code_groups:
                logger.warning(
                    "No custom code groups defined for 'custom' level encoding"
                )
                return {}
            for group_name in self.custom_code_groups.keys():
                feature_name = f"icd10_custom_{group_name}_count"
                features[feature_name] = 0
            for code in codes:
                normalized = self.normalize_icd10(code)
                if not normalized:
                    continue
                for group_name, code_list in self.custom_code_groups.items():
                    if any(
                        (
                            normalized.startswith(self.normalize_icd10(c))
                            for c in code_list
                        )
                    ):
                        feature_name = f"icd10_custom_{group_name}_count"
                        features[feature_name] = features.get(feature_name, 0) + 1
        else:
            logger.error(f"Unsupported encoding level: {level}")
            return {}
        return features

    def transform(
        self,
        df: pd.DataFrame,
        code_column: str,
        patient_id_column: Optional[str] = None,
        encoding_type: str = "binary",
        encoding_level: str = "chapter",
    ) -> pd.DataFrame:
        """
        Transform a DataFrame with ICD-10 codes into features.

        Args:
            df: Input DataFrame with ICD-10 codes
            code_column: Column name containing ICD-10 codes
            patient_id_column: Column name for patient ID (for grouping)
            encoding_type: Type of encoding ('binary' or 'count')
            encoding_level: Level of encoding ('chapter', 'category', 'group', or 'custom')

        Returns:
            DataFrame with encoded features
        """
        if code_column not in df.columns:
            raise ValueError(f"Column '{code_column}' not found in DataFrame")
        if patient_id_column and patient_id_column not in df.columns:
            raise ValueError(f"Column '{patient_id_column}' not found in DataFrame")
        if patient_id_column:
            patient_codes = (
                df.groupby(patient_id_column)[code_column].apply(list).to_dict()
            )
            patient_features = {}
            for patient_id, codes in patient_codes.items():
                if encoding_type == "binary":
                    features = self.encode_codes_binary(codes, encoding_level)
                elif encoding_type == "count":
                    features = self.encode_codes_count(codes, encoding_level)
                else:
                    raise ValueError(f"Unsupported encoding type: {encoding_type}")
                patient_features[patient_id] = features
            features_df = pd.DataFrame.from_dict(patient_features, orient="index")
            features_df = features_df.fillna(0)
            features_df.index.name = patient_id_column
            return features_df
        else:
            features_list = []
            for _, row in df.iterrows():
                code = row[code_column]
                codes = [code] if isinstance(code, str) else code
                if encoding_type == "binary":
                    features = self.encode_codes_binary(codes, encoding_level)
                elif encoding_type == "count":
                    features = self.encode_codes_count(codes, encoding_level)
                else:
                    raise ValueError(f"Unsupported encoding type: {encoding_type}")
                features_list.append(features)
            features_df = pd.DataFrame(features_list)
            features_df = features_df.fillna(0)
            result = pd.concat(
                [df.reset_index(drop=True), features_df.reset_index(drop=True)], axis=1
            )
            return result
