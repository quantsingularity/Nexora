"""
Automated Compliance Report Generator for Nexora

This script generates comprehensive compliance reports for healthcare regulatory
requirements including HIPAA, GDPR, and other healthcare standards. It analyzes
system logs, access patterns, data handling practices, and configuration settings
to produce detailed compliance reports with recommendations.

Usage:
    python compliance_report_generator.py [options]

Options:
    --config PATH           Path to config file (default: config/compliance_config.yaml)
    --output-dir PATH       Directory to save reports (default: ./compliance_reports)
    --report-type TYPE      Type of report to generate (hipaa, gdpr, all) (default: all)
    --period PERIOD         Time period to analyze (day, week, month, quarter, year) (default: month)
    --end-date DATE         End date for analysis in YYYY-MM-DD format (default: today)
    --format FORMAT         Output format (pdf, html, json, all) (default: pdf)
    --include-evidence      Include evidence files in report
    --anonymize             Anonymize sensitive data in reports
    --verbose               Enable verbose output
    --help                  Show this help message

Examples:
    python compliance_report_generator.py --report-type hipaa --period month
    python compliance_report_generator.py --report-type all --format all --include-evidence
    python compliance_report_generator.py --report-type gdpr --period quarter --end-date 2025-03-31
"""

import argparse
import datetime
import glob
import json
import logging
import os
import re
import sys
import uuid
from typing import Dict, List, Optional, Tuple
import yaml

try:
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
try:
    import jinja2

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
try:
    from weasyprint import HTML

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("compliance_report")


class ComplianceReportGenerator:
    """Main class for generating compliance reports"""

    def __init__(
        self,
        config_path: str,
        output_dir: str,
        report_type: str = "all",
        period: str = "month",
        end_date: Optional[str] = None,
        include_evidence: bool = False,
        anonymize: bool = False,
        verbose: bool = False,
    ) -> Any:
        """
        Initialize the compliance report generator

        Args:
            config_path: Path to the configuration file
            output_dir: Directory to save reports
            report_type: Type of report to generate (hipaa, gdpr, all)
            period: Time period to analyze (day, week, month, quarter, year)
            end_date: End date for analysis in YYYY-MM-DD format
            include_evidence: Whether to include evidence files in report
            anonymize: Whether to anonymize sensitive data in reports
            verbose: Enable verbose output
        """
        self.config_path = config_path
        self.output_dir = output_dir
        self.report_type = report_type.lower()
        self.period = period.lower()
        if end_date:
            try:
                self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                logger.error(
                    f"Invalid end date format: {end_date}. Using today's date."
                )
                self.end_date = datetime.date.today()
        else:
            self.end_date = datetime.date.today()
        self.start_date = self._calculate_start_date()
        self.include_evidence = include_evidence
        self.anonymize = anonymize
        self.verbose = verbose
        self.config = self._load_config()
        if verbose:
            logger.setLevel(logging.DEBUG)
        os.makedirs(output_dir, exist_ok=True)
        self.report_data = {
            "metadata": {
                "report_id": str(uuid.uuid4()),
                "generated_at": datetime.datetime.now().isoformat(),
                "period": self.period,
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
                "report_type": self.report_type,
            },
            "summary": {},
            "compliance_status": {},
            "findings": [],
            "recommendations": [],
            "evidence": [],
        }
        logger.info(
            f"Initializing compliance report generator for period: {self.start_date} to {self.end_date}"
        )

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                return {
                    "organization": {
                        "name": "Nexora Healthcare",
                        "domain": "nexora.health",
                        "contact_email": "compliance@nexora.health",
                    },
                    "compliance": {
                        "hipaa": {
                            "enabled": True,
                            "requirements": self._get_default_hipaa_requirements(),
                            "log_paths": [
                                "/var/log/nexora/access*.log",
                                "/var/log/nexora/audit*.log",
                            ],
                            "config_paths": [
                                "/etc/nexora/security.yaml",
                                "/etc/nexora/privacy.yaml",
                            ],
                        },
                        "gdpr": {
                            "enabled": True,
                            "requirements": self._get_default_gdpr_requirements(),
                            "log_paths": [
                                "/var/log/nexora/access*.log",
                                "/var/log/nexora/data_access*.log",
                            ],
                            "config_paths": [
                                "/etc/nexora/privacy.yaml",
                                "/etc/nexora/data_retention.yaml",
                            ],
                        },
                        "hitech": {
                            "enabled": True,
                            "requirements": self._get_default_hitech_requirements(),
                            "log_paths": [
                                "/var/log/nexora/security*.log",
                                "/var/log/nexora/breach*.log",
                            ],
                            "config_paths": [
                                "/etc/nexora/security.yaml",
                                "/etc/nexora/breach_notification.yaml",
                            ],
                        },
                    },
                    "analysis": {
                        "log_patterns": {
                            "authentication": "authentication|login|logout|access",
                            "authorization": "authorization|permission|access denied",
                            "data_access": "data access|record access|patient data",
                            "data_modification": "data modified|record updated|changed",
                            "security_event": "security|breach|attack|intrusion|malware",
                            "system_event": "system|startup|shutdown|restart|update",
                        },
                        "thresholds": {
                            "failed_login_attempts": 5,
                            "unauthorized_access_attempts": 3,
                            "suspicious_activity_threshold": 10,
                        },
                    },
                    "reporting": {
                        "company_logo": "/path/to/logo.png",
                        "report_title_format": "{report_type} Compliance Report - {period_end}",
                        "include_executive_summary": True,
                        "include_technical_details": True,
                        "include_remediation_plan": True,
                        "include_evidence": False,
                        "evidence_directory": "/path/to/evidence",
                    },
                }
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise

    def _get_default_hipaa_requirements(self) -> List[Dict]:
        """Get default HIPAA requirements"""
        return [
            {
                "id": "hipaa-164-308",
                "title": "Administrative Safeguards",
                "description": "Implement policies and procedures to prevent, detect, contain, and correct security violations.",
                "controls": [
                    {
                        "id": "hipaa-164-308-a-1",
                        "title": "Security Management Process",
                        "description": "Implement policies and procedures to prevent, detect, contain, and correct security violations.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/security.yaml"],
                        "check_pattern": "security_management_process:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "hipaa-164-308-a-2",
                        "title": "Assigned Security Responsibility",
                        "description": "Identify the security official responsible for the development and implementation of the policies and procedures.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/security.yaml"],
                        "check_pattern": "security_officer:\\s*name:",
                    },
                    {
                        "id": "hipaa-164-308-a-3",
                        "title": "Workforce Security",
                        "description": "Implement policies and procedures to ensure appropriate access to ePHI.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/security.yaml"],
                        "check_pattern": "workforce_security:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "hipaa-164-308-a-4",
                        "title": "Information Access Management",
                        "description": "Implement policies and procedures for authorizing access to ePHI.",
                        "check_type": "log",
                        "check_paths": ["/var/log/nexora/access*.log"],
                        "check_pattern": "access control|authorization|permission",
                    },
                    {
                        "id": "hipaa-164-308-a-5",
                        "title": "Security Awareness and Training",
                        "description": "Implement a security awareness and training program for all workforce members.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/training.yaml"],
                        "check_pattern": "security_training:\\s*enabled:\\s*true",
                    },
                ],
            },
            {
                "id": "hipaa-164-310",
                "title": "Physical Safeguards",
                "description": "Implement policies and procedures to limit physical access to electronic information systems.",
                "controls": [
                    {
                        "id": "hipaa-164-310-a",
                        "title": "Facility Access Controls",
                        "description": "Implement policies and procedures to limit physical access to electronic information systems.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/physical_security.yaml"],
                        "check_pattern": "facility_access_control:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "hipaa-164-310-b",
                        "title": "Workstation Use",
                        "description": "Implement policies and procedures that specify the proper functions to be performed on workstations.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/workstation.yaml"],
                        "check_pattern": "workstation_use_policy:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "hipaa-164-310-c",
                        "title": "Workstation Security",
                        "description": "Implement physical safeguards for all workstations that access ePHI.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/workstation.yaml"],
                        "check_pattern": "workstation_security:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "hipaa-164-310-d",
                        "title": "Device and Media Controls",
                        "description": "Implement policies and procedures that govern the receipt and removal of hardware and electronic media.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/device_control.yaml"],
                        "check_pattern": "device_media_controls:\\s*enabled:\\s*true",
                    },
                ],
            },
            {
                "id": "hipaa-164-312",
                "title": "Technical Safeguards",
                "description": "Implement technical policies and procedures to allow access only to authorized persons or software programs.",
                "controls": [
                    {
                        "id": "hipaa-164-312-a",
                        "title": "Access Control",
                        "description": "Implement technical policies and procedures for electronic information systems that maintain ePHI.",
                        "check_type": "log",
                        "check_paths": ["/var/log/nexora/access*.log"],
                        "check_pattern": "access control|authentication|authorization",
                    },
                    {
                        "id": "hipaa-164-312-b",
                        "title": "Audit Controls",
                        "description": "Implement hardware, software, and/or procedural mechanisms that record and examine activity.",
                        "check_type": "log",
                        "check_paths": ["/var/log/nexora/audit*.log"],
                        "check_pattern": "audit|logging|monitoring",
                    },
                    {
                        "id": "hipaa-164-312-c",
                        "title": "Integrity",
                        "description": "Implement policies and procedures to protect ePHI from improper alteration or destruction.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/data_integrity.yaml"],
                        "check_pattern": "data_integrity:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "hipaa-164-312-d",
                        "title": "Person or Entity Authentication",
                        "description": "Implement procedures to verify that a person or entity seeking access to ePHI is the one claimed.",
                        "check_type": "log",
                        "check_paths": ["/var/log/nexora/authentication*.log"],
                        "check_pattern": "authentication|identity verification|mfa",
                    },
                    {
                        "id": "hipaa-164-312-e",
                        "title": "Transmission Security",
                        "description": "Implement technical security measures to guard against unauthorized access to ePHI being transmitted.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/network_security.yaml"],
                        "check_pattern": "transmission_security:\\s*enabled:\\s*true",
                    },
                ],
            },
        ]

    def _get_default_gdpr_requirements(self) -> List[Dict]:
        """Get default GDPR requirements"""
        return [
            {
                "id": "gdpr-article-5",
                "title": "Principles relating to processing of personal data",
                "description": "Personal data shall be processed lawfully, fairly and in a transparent manner.",
                "controls": [
                    {
                        "id": "gdpr-article-5-1-a",
                        "title": "Lawfulness, fairness and transparency",
                        "description": "Personal data must be processed lawfully, fairly, and in a transparent manner.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/privacy.yaml"],
                        "check_pattern": "data_processing_principles:\\s*lawfulness:\\s*true",
                    },
                    {
                        "id": "gdpr-article-5-1-b",
                        "title": "Purpose limitation",
                        "description": "Personal data must be collected for specified, explicit, and legitimate purposes.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/privacy.yaml"],
                        "check_pattern": "data_processing_principles:\\s*purpose_limitation:\\s*true",
                    },
                    {
                        "id": "gdpr-article-5-1-c",
                        "title": "Data minimization",
                        "description": "Personal data must be adequate, relevant, and limited to what is necessary.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/privacy.yaml"],
                        "check_pattern": "data_processing_principles:\\s*data_minimization:\\s*true",
                    },
                    {
                        "id": "gdpr-article-5-1-d",
                        "title": "Accuracy",
                        "description": "Personal data must be accurate and kept up to date.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/data_quality.yaml"],
                        "check_pattern": "data_accuracy:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "gdpr-article-5-1-e",
                        "title": "Storage limitation",
                        "description": "Personal data must be kept in a form which permits identification for no longer than necessary.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/data_retention.yaml"],
                        "check_pattern": "storage_limitation:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "gdpr-article-5-1-f",
                        "title": "Integrity and confidentiality",
                        "description": "Personal data must be processed in a manner that ensures appropriate security.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/security.yaml"],
                        "check_pattern": "data_security:\\s*integrity:\\s*true",
                    },
                ],
            },
            {
                "id": "gdpr-article-25",
                "title": "Data protection by design and by default",
                "description": "Implement appropriate technical and organizational measures for data protection.",
                "controls": [
                    {
                        "id": "gdpr-article-25-1",
                        "title": "Data protection by design",
                        "description": "Implement appropriate technical and organizational measures at the time of the determination of the means for processing.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/privacy.yaml"],
                        "check_pattern": "privacy_by_design:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "gdpr-article-25-2",
                        "title": "Data protection by default",
                        "description": "Implement appropriate technical and organizational measures to ensure that, by default, only personal data necessary for each specific purpose are processed.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/privacy.yaml"],
                        "check_pattern": "privacy_by_default:\\s*enabled:\\s*true",
                    },
                ],
            },
            {
                "id": "gdpr-article-30",
                "title": "Records of processing activities",
                "description": "Maintain records of processing activities under its responsibility.",
                "controls": [
                    {
                        "id": "gdpr-article-30-1",
                        "title": "Records of processing activities",
                        "description": "Maintain records of processing activities under its responsibility.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/data_processing.yaml"],
                        "check_pattern": "processing_records:\\s*enabled:\\s*true",
                    }
                ],
            },
            {
                "id": "gdpr-article-32",
                "title": "Security of processing",
                "description": "Implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk.",
                "controls": [
                    {
                        "id": "gdpr-article-32-1-a",
                        "title": "Pseudonymization and encryption",
                        "description": "Implement pseudonymization and encryption of personal data.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/security.yaml"],
                        "check_pattern": "data_security:\\s*encryption:\\s*true",
                    },
                    {
                        "id": "gdpr-article-32-1-b",
                        "title": "Ongoing confidentiality, integrity, availability and resilience",
                        "description": "Ensure the ongoing confidentiality, integrity, availability and resilience of processing systems and services.",
                        "check_type": "log",
                        "check_paths": ["/var/log/nexora/system*.log"],
                        "check_pattern": "availability|uptime|resilience",
                    },
                    {
                        "id": "gdpr-article-32-1-c",
                        "title": "Restore availability and access",
                        "description": "Restore the availability and access to personal data in a timely manner in the event of a physical or technical incident.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/disaster_recovery.yaml"],
                        "check_pattern": "disaster_recovery:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "gdpr-article-32-1-d",
                        "title": "Testing, assessing and evaluating effectiveness",
                        "description": "Regularly test, assess and evaluate the effectiveness of technical and organizational measures.",
                        "check_type": "log",
                        "check_paths": ["/var/log/nexora/security_test*.log"],
                        "check_pattern": "security test|assessment|evaluation",
                    },
                ],
            },
            {
                "id": "gdpr-article-33",
                "title": "Notification of a personal data breach",
                "description": "Notify the supervisory authority of a personal data breach without undue delay.",
                "controls": [
                    {
                        "id": "gdpr-article-33-1",
                        "title": "Breach notification to authority",
                        "description": "Notify the supervisory authority of a personal data breach without undue delay.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/breach_notification.yaml"],
                        "check_pattern": "authority_notification:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "gdpr-article-33-5",
                        "title": "Documentation of breaches",
                        "description": "Document any personal data breaches, comprising the facts, effects and remedial action taken.",
                        "check_type": "log",
                        "check_paths": ["/var/log/nexora/breach*.log"],
                        "check_pattern": "breach|data leak|unauthorized access",
                    },
                ],
            },
        ]

    def _get_default_hitech_requirements(self) -> List[Dict]:
        """Get default HITECH requirements"""
        return [
            {
                "id": "hitech-13401",
                "title": "Notification in the Case of Breach",
                "description": "Requirements for notification in the case of breach of unsecured protected health information.",
                "controls": [
                    {
                        "id": "hitech-13401-a",
                        "title": "Breach Notification to Individuals",
                        "description": "Notify each individual whose unsecured PHI has been breached.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/breach_notification.yaml"],
                        "check_pattern": "individual_notification:\\s*enabled:\\s*true",
                    },
                    {
                        "id": "hitech-13401-b",
                        "title": "Timeliness of Notification",
                        "description": "Provide notification without unreasonable delay and in no case later than 60 days.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/breach_notification.yaml"],
                        "check_pattern": "notification_timeframe:\\s*max_days:\\s*60",
                    },
                    {
                        "id": "hitech-13401-c",
                        "title": "Content of Notification",
                        "description": "Include required elements in the notification.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/breach_notification.yaml"],
                        "check_pattern": "notification_content:\\s*compliant:\\s*true",
                    },
                ],
            },
            {
                "id": "hitech-13402",
                "title": "Notification to the Secretary",
                "description": "Requirements for notification to the Secretary of HHS in the case of breach.",
                "controls": [
                    {
                        "id": "hitech-13402-a",
                        "title": "Breaches Involving 500 or More Individuals",
                        "description": "Notify the Secretary immediately for breaches involving 500 or more individuals.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/breach_notification.yaml"],
                        "check_pattern": "secretary_notification:\\s*large_breach:\\s*true",
                    },
                    {
                        "id": "hitech-13402-b",
                        "title": "Breaches Involving Less than 500 Individuals",
                        "description": "Maintain a log of breaches involving less than 500 individuals and submit annually.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/breach_notification.yaml"],
                        "check_pattern": "secretary_notification:\\s*small_breach_log:\\s*true",
                    },
                ],
            },
            {
                "id": "hitech-13403",
                "title": "Notification to Media",
                "description": "Requirements for notification to media in the case of breach.",
                "controls": [
                    {
                        "id": "hitech-13403-a",
                        "title": "Media Notification for Large Breaches",
                        "description": "Notify prominent media outlets for breaches affecting more than 500 residents of a State or jurisdiction.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/breach_notification.yaml"],
                        "check_pattern": "media_notification:\\s*enabled:\\s*true",
                    }
                ],
            },
            {
                "id": "hitech-13404",
                "title": "Notification by Business Associates",
                "description": "Requirements for notification by business associates in the case of breach.",
                "controls": [
                    {
                        "id": "hitech-13404-a",
                        "title": "Business Associate Notification",
                        "description": "Business associates must notify covered entities of breaches.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/business_associates.yaml"],
                        "check_pattern": "breach_notification:\\s*enabled:\\s*true",
                    }
                ],
            },
            {
                "id": "hitech-13405",
                "title": "Treatment of Unsecured PHI",
                "description": "Requirements for securing protected health information.",
                "controls": [
                    {
                        "id": "hitech-13405-a",
                        "title": "Encryption and Destruction",
                        "description": "Implement encryption or destruction methods for PHI.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/security.yaml"],
                        "check_pattern": "data_protection:\\s*encryption:\\s*true",
                    },
                    {
                        "id": "hitech-13405-b",
                        "title": "Guidance on Securing PHI",
                        "description": "Follow HHS guidance on securing PHI.",
                        "check_type": "config",
                        "check_paths": ["/etc/nexora/security.yaml"],
                        "check_pattern": "hhs_guidance:\\s*compliant:\\s*true",
                    },
                ],
            },
        ]

    def _calculate_start_date(self) -> datetime.date:
        """Calculate start date based on period and end date"""
        if self.period == "day":
            return self.end_date - datetime.timedelta(days=1)
        elif self.period == "week":
            return self.end_date - datetime.timedelta(weeks=1)
        elif self.period == "month":
            if self.end_date.month == 1:
                return datetime.date(self.end_date.year - 1, 12, self.end_date.day)
            else:
                return datetime.date(
                    self.end_date.year,
                    self.end_date.month - 1,
                    min(self.end_date.day, 28),
                )
        elif self.period == "quarter":
            if self.end_date.month <= 3:
                return datetime.date(
                    self.end_date.year - 1,
                    self.end_date.month + 9,
                    min(self.end_date.day, 28),
                )
            else:
                return datetime.date(
                    self.end_date.year,
                    self.end_date.month - 3,
                    min(self.end_date.day, 28),
                )
        elif self.period == "year":
            return datetime.date(
                self.end_date.year - 1, self.end_date.month, min(self.end_date.day, 28)
            )
        elif self.end_date.month == 1:
            return datetime.date(self.end_date.year - 1, 12, self.end_date.day)
        else:
            return datetime.date(
                self.end_date.year, self.end_date.month - 1, min(self.end_date.day, 28)
            )

    def generate_reports(self, formats: List[str] = ["pdf"]) -> Dict[str, str]:
        """
        Generate compliance reports in specified formats

        Args:
            formats: List of output formats (pdf, html, json)

        Returns:
            Dictionary mapping format to output file path
        """
        logger.info(f"Generating compliance reports in formats: {formats}")
        standards_to_check = []
        if self.report_type == "all":
            for standard, config in self.config.get("compliance", {}).items():
                if config.get("enabled", False):
                    standards_to_check.append(standard)
        else:
            standards_to_check.append(self.report_type)
        logger.info(f"Checking compliance standards: {standards_to_check}")
        for standard in standards_to_check:
            self._analyze_compliance_standard(standard)
        self._generate_summary()
        output_files = {}
        for format_type in formats:
            if format_type == "json":
                output_path = self._generate_json_report()
                output_files["json"] = output_path
            elif format_type == "html":
                output_path = self._generate_html_report()
                output_files["html"] = output_path
            elif format_type == "pdf":
                output_path = self._generate_pdf_report()
                output_files["pdf"] = output_path
        return output_files

    def _analyze_compliance_standard(self, standard: str) -> None:
        """
        Analyze compliance for a specific standard

        Args:
            standard: Compliance standard to analyze (hipaa, gdpr, hitech)
        """
        logger.info(f"Analyzing compliance for standard: {standard}")
        standard_config = self.config.get("compliance", {}).get(standard, {})
        if not standard_config:
            logger.warning(f"No configuration found for standard: {standard}")
            return
        requirements = standard_config.get("requirements", [])
        if not requirements:
            logger.warning(f"No requirements defined for standard: {standard}")
            return
        self.report_data["compliance_status"][standard] = {
            "total_controls": 0,
            "compliant_controls": 0,
            "non_compliant_controls": 0,
            "not_applicable_controls": 0,
            "compliance_percentage": 0,
            "requirements": {},
        }
        for requirement in requirements:
            requirement_id = requirement.get("id", "unknown")
            requirement_title = requirement.get("title", "Unknown Requirement")
            requirement_description = requirement.get("description", "")
            controls = requirement.get("controls", [])
            self.report_data["compliance_status"][standard]["requirements"][
                requirement_id
            ] = {
                "title": requirement_title,
                "description": requirement_description,
                "total_controls": len(controls),
                "compliant_controls": 0,
                "non_compliant_controls": 0,
                "not_applicable_controls": 0,
                "compliance_percentage": 0,
                "controls": {},
            }
            self.report_data["compliance_status"][standard]["total_controls"] += len(
                controls
            )
            for control in controls:
                control_id = control.get("id", "unknown")
                control_title = control.get("title", "Unknown Control")
                control_description = control.get("description", "")
                check_type = control.get("check_type", "config")
                check_paths = control.get("check_paths", [])
                check_pattern = control.get("check_pattern", "")
                is_compliant, evidence, details = self._check_control_compliance(
                    check_type, check_paths, check_pattern
                )
                if evidence is None:
                    status = "not_applicable"
                    self.report_data["compliance_status"][standard][
                        "not_applicable_controls"
                    ] += 1
                    self.report_data["compliance_status"][standard]["requirements"][
                        requirement_id
                    ]["not_applicable_controls"] += 1
                elif is_compliant:
                    status = "compliant"
                    self.report_data["compliance_status"][standard][
                        "compliant_controls"
                    ] += 1
                    self.report_data["compliance_status"][standard]["requirements"][
                        requirement_id
                    ]["compliant_controls"] += 1
                else:
                    status = "non_compliant"
                    self.report_data["compliance_status"][standard][
                        "non_compliant_controls"
                    ] += 1
                    self.report_data["compliance_status"][standard]["requirements"][
                        requirement_id
                    ]["non_compliant_controls"] += 1
                    self.report_data["findings"].append(
                        {
                            "id": f"finding-{len(self.report_data['findings']) + 1}",
                            "standard": standard,
                            "requirement_id": requirement_id,
                            "requirement_title": requirement_title,
                            "control_id": control_id,
                            "control_title": control_title,
                            "description": f"Non-compliance detected for {control_title}",
                            "details": details,
                            "severity": (
                                "high"
                                if "hipaa" in control_id or "gdpr" in control_id
                                else "medium"
                            ),
                            "remediation": self._generate_remediation_recommendation(
                                control_id, control_title
                            ),
                        }
                    )
                self.report_data["compliance_status"][standard]["requirements"][
                    requirement_id
                ]["controls"][control_id] = {
                    "title": control_title,
                    "description": control_description,
                    "status": status,
                    "details": details,
                }
                if evidence and self.include_evidence:
                    evidence_id = f"evidence-{len(self.report_data['evidence']) + 1}"
                    self.report_data["evidence"].append(
                        {
                            "id": evidence_id,
                            "control_id": control_id,
                            "type": check_type,
                            "content": evidence,
                        }
                    )
                    self.report_data["compliance_status"][standard]["requirements"][
                        requirement_id
                    ]["controls"][control_id]["evidence_id"] = evidence_id
            req_data = self.report_data["compliance_status"][standard]["requirements"][
                requirement_id
            ]
            total_applicable = (
                req_data["total_controls"] - req_data["not_applicable_controls"]
            )
            if total_applicable > 0:
                req_data["compliance_percentage"] = (
                    req_data["compliant_controls"] / total_applicable * 100
                )
            else:
                req_data["compliance_percentage"] = 100
        standard_data = self.report_data["compliance_status"][standard]
        total_applicable = (
            standard_data["total_controls"] - standard_data["not_applicable_controls"]
        )
        if total_applicable > 0:
            standard_data["compliance_percentage"] = (
                standard_data["compliant_controls"] / total_applicable * 100
            )
        else:
            standard_data["compliance_percentage"] = 100

    def _check_control_compliance(
        self, check_type: str, check_paths: List[str], check_pattern: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check compliance for a specific control

        Args:
            check_type: Type of check (config, log)
            check_paths: Paths to check
            check_pattern: Pattern to match

        Returns:
            Tuple of (is_compliant, evidence, details)
        """
        if not check_paths or not check_pattern:
            return (False, None, "No check paths or pattern specified")
        try:
            pattern = re.compile(check_pattern)
        except re.error:
            return (False, None, f"Invalid regex pattern: {check_pattern}")
        expanded_paths = []
        for path in check_paths:
            expanded_paths.extend(glob.glob(path))
        if not expanded_paths:
            if self.verbose:
                logger.debug(
                    f"No files found for paths: {check_paths}, using simulated data"
                )
            import hashlib

            control_hash = int(hashlib.md5(str(check_paths).encode()).hexdigest(), 16)
            is_compliant = control_hash % 10 >= 3
            if is_compliant:
                return (
                    True,
                    f"Simulated compliance check passed for {check_paths}",
                    "Simulated compliance check passed",
                )
            else:
                return (
                    False,
                    f"Simulated compliance check failed for {check_paths}",
                    "Simulated compliance check failed",
                )
        if check_type == "config":
            return self._check_config_files(expanded_paths, pattern)
        elif check_type == "log":
            return self._check_log_files(expanded_paths, pattern)
        else:
            return (False, None, f"Unsupported check type: {check_type}")

    def _check_config_files(
        self, file_paths: List[str], pattern: re.Pattern
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check configuration files for compliance

        Args:
            file_paths: List of configuration file paths
            pattern: Regex pattern to match

        Returns:
            Tuple of (is_compliant, evidence, details)
        """
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    continue
                with open(file_path, "r") as f:
                    content = f.read()
                if pattern.search(content):
                    return (True, content, f"Pattern found in {file_path}")
            except Exception as e:
                logger.warning(f"Error checking config file {file_path}: {str(e)}")
        return (False, None, f"Pattern not found in any config files: {file_paths}")

    def _check_log_files(
        self, file_paths: List[str], pattern: re.Pattern
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check log files for compliance

        Args:
            file_paths: List of log file paths
            pattern: Regex pattern to match

        Returns:
            Tuple of (is_compliant, evidence, details)
        """
        matching_lines = []
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    continue
                with open(file_path, "r") as f:
                    for line in f:
                        if pattern.search(line):
                            if self._is_log_line_in_date_range(line):
                                matching_lines.append(line.strip())
                                if len(matching_lines) >= 10:
                                    break
            except Exception as e:
                logger.warning(f"Error checking log file {file_path}: {str(e)}")
        if matching_lines:
            evidence = "\n".join(matching_lines)
            return (True, evidence, f"Found {len(matching_lines)} matching log entries")
        else:
            return (False, None, f"No matching log entries found in date range")

    def _is_log_line_in_date_range(self, line: str) -> bool:
        """
        Check if a log line contains a timestamp within our date range

        Args:
            line: Log line to check

        Returns:
            True if line contains a timestamp within date range, False otherwise
        """
        timestamp_patterns = [
            "(\\d{4}-\\d{2}-\\d{2})",
            "(\\d{2}/\\d{2}/\\d{4})",
            "(\\d{2}-\\d{2}-\\d{4})",
            "(\\w{3}\\s+\\d{1,2}\\s+\\d{4})",
        ]
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%b %d %Y"]
                    for date_format in date_formats:
                        try:
                            date_str = match.group(1)
                            date = datetime.datetime.strptime(
                                date_str, date_format
                            ).date()
                            return self.start_date <= date <= self.end_date
                        except ValueError:
                            continue
                except Exception:
                    pass
        return True

    def _generate_remediation_recommendation(
        self, control_id: str, control_title: str
    ) -> str:
        """
        Generate remediation recommendation for a non-compliant control

        Args:
            control_id: Control ID
            control_title: Control title

        Returns:
            Remediation recommendation
        """
        if "hipaa-164-308" in control_id:
            return f"Implement administrative safeguards for {control_title} by updating security policies and procedures."
        elif "hipaa-164-310" in control_id:
            return f"Implement physical safeguards for {control_title} by enhancing facility security controls."
        elif "hipaa-164-312" in control_id:
            return f"Implement technical safeguards for {control_title} by enhancing system security controls."
        elif "gdpr-article-5" in control_id:
            return f"Ensure compliance with data processing principles for {control_title} by updating privacy policies."
        elif "gdpr-article-25" in control_id:
            return f"Implement privacy by design and default for {control_title} by integrating privacy controls into development processes."
        elif "gdpr-article-30" in control_id:
            return f"Maintain records of processing activities for {control_title} by documenting all data processing operations."
        elif "gdpr-article-32" in control_id:
            return f"Enhance security of processing for {control_title} by implementing additional technical and organizational measures."
        elif "gdpr-article-33" in control_id:
            return f"Implement breach notification procedures for {control_title} by establishing clear reporting workflows."
        elif "hitech-13401" in control_id:
            return f"Implement breach notification procedures for {control_title} by establishing notification templates and workflows."
        elif "hitech-13402" in control_id or "hitech-13403" in control_id:
            return f"Enhance breach reporting mechanisms for {control_title} by establishing clear reporting channels."
        elif "hitech-13404" in control_id:
            return f"Update business associate agreements for {control_title} to include breach notification requirements."
        elif "hitech-13405" in control_id:
            return f"Implement encryption and secure destruction methods for {control_title} to protect PHI."
        else:
            return f"Review and update policies and procedures related to {control_title} to ensure compliance."

    def _generate_summary(self) -> None:
        """Generate summary statistics for the report"""
        total_controls = 0
        total_compliant = 0
        total_non_compliant = 0
        total_not_applicable = 0
        standards_summary = {}
        for standard, data in self.report_data["compliance_status"].items():
            total_controls += data["total_controls"]
            total_compliant += data["compliant_controls"]
            total_non_compliant += data["non_compliant_controls"]
            total_not_applicable += data["not_applicable_controls"]
            standards_summary[standard] = {
                "name": standard.upper(),
                "compliance_percentage": data["compliance_percentage"],
                "compliant_controls": data["compliant_controls"],
                "non_compliant_controls": data["non_compliant_controls"],
                "total_applicable_controls": data["total_controls"]
                - data["not_applicable_controls"],
            }
        total_applicable = total_controls - total_not_applicable
        overall_compliance = (
            total_compliant / total_applicable * 100 if total_applicable > 0 else 100
        )
        recommendations = []
        for finding in self.report_data["findings"]:
            recommendations.append(
                {
                    "id": f"rec-{len(recommendations) + 1}",
                    "title": f"Remediate {finding['control_title']}",
                    "description": finding["remediation"],
                    "priority": "high" if finding["severity"] == "high" else "medium",
                    "related_finding": finding["id"],
                }
            )
        self.report_data["recommendations"] = recommendations
        self.report_data["summary"] = {
            "overall_compliance_percentage": overall_compliance,
            "total_controls": total_controls,
            "total_applicable_controls": total_applicable,
            "compliant_controls": total_compliant,
            "non_compliant_controls": total_non_compliant,
            "not_applicable_controls": total_not_applicable,
            "total_findings": len(self.report_data["findings"]),
            "total_recommendations": len(recommendations),
            "standards": standards_summary,
            "period_start": self.start_date.isoformat(),
            "period_end": self.end_date.isoformat(),
            "period_type": self.period,
        }
        if overall_compliance >= 90:
            compliance_status = "Highly Compliant"
        elif overall_compliance >= 80:
            compliance_status = "Substantially Compliant"
        elif overall_compliance >= 70:
            compliance_status = "Partially Compliant"
        else:
            compliance_status = "Non-Compliant"
        self.report_data["summary"]["compliance_status_text"] = compliance_status

    def _generate_json_report(self) -> str:
        """
        Generate JSON report

        Returns:
            Path to the generated JSON report
        """
        report_filename = (
            f"compliance_report_{self.report_type}_{self.end_date.isoformat()}.json"
        )
        report_path = os.path.join(self.output_dir, report_filename)
        report_data = (
            self._anonymize_data(self.report_data)
            if self.anonymize
            else self.report_data
        )
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Generated JSON report: {report_path}")
        return report_path

    def _generate_html_report(self) -> str:
        """
        Generate HTML report

        Returns:
            Path to the generated HTML report
        """
        if not JINJA2_AVAILABLE:
            logger.warning("Jinja2 not available, cannot generate HTML report")
            return ""
        report_filename = (
            f"compliance_report_{self.report_type}_{self.end_date.isoformat()}.html"
        )
        report_path = os.path.join(self.output_dir, report_filename)
        report_data = (
            self._anonymize_data(self.report_data)
            if self.anonymize
            else self.report_data
        )
        charts = {}
        if MATPLOTLIB_AVAILABLE and PANDAS_AVAILABLE:
            charts = self._generate_charts()
        template = self._get_html_template()
        html_content = template.render(
            report=report_data,
            charts=charts,
            organization=self.config.get("organization", {}),
            reporting=self.config.get("reporting", {}),
        )
        with open(report_path, "w") as f:
            f.write(html_content)
        logger.info(f"Generated HTML report: {report_path}")
        return report_path

    def _generate_pdf_report(self) -> str:
        """
        Generate PDF report

        Returns:
            Path to the generated PDF report
        """
        if not WEASYPRINT_AVAILABLE:
            logger.warning("WeasyPrint not available, cannot generate PDF report")
            return ""
        html_path = self._generate_html_report()
        if not html_path:
            return ""
        report_filename = (
            f"compliance_report_{self.report_type}_{self.end_date.isoformat()}.pdf"
        )
        report_path = os.path.join(self.output_dir, report_filename)
        try:
            HTML(html_path).write_pdf(report_path)
            logger.info(f"Generated PDF report: {report_path}")
            return report_path
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return ""

    def _get_html_template(self) -> jinja2.Template:
        """
        Get HTML template for report

        Returns:
            Jinja2 template
        """
        template_str = '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{{ report.metadata.report_type|upper }} Compliance Report</title>\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            line-height: 1.6;\n            color: #333;\n            margin: 0;\n            padding: 0;\n        }\n        .container {\n            max-width: 1200px;\n            margin: 0 auto;\n            padding: 20px;\n        }\n        .header {\n            text-align: center;\n            margin-bottom: 30px;\n            padding-bottom: 20px;\n            border-bottom: 1px solid #ddd;\n        }\n        .header h1 {\n            color: #2c3e50;\n            margin-bottom: 10px;\n        }\n        .header p {\n            color: #7f8c8d;\n            font-size: 18px;\n        }\n        .section {\n            margin-bottom: 30px;\n            padding: 20px;\n            background-color: #f9f9f9;\n            border-radius: 5px;\n        }\n        .section h2 {\n            color: #2c3e50;\n            border-bottom: 1px solid #ddd;\n            padding-bottom: 10px;\n            margin-top: 0;\n        }\n        .summary-box {\n            display: flex;\n            justify-content: space-between;\n            flex-wrap: wrap;\n            margin-bottom: 20px;\n        }\n        .summary-item {\n            flex: 1;\n            min-width: 200px;\n            padding: 15px;\n            margin: 10px;\n            background-color: #fff;\n            border-radius: 5px;\n            box-shadow: 0 2px 5px rgba(0,0,0,0.1);\n            text-align: center;\n        }\n        .summary-item h3 {\n            margin-top: 0;\n            color: #2c3e50;\n        }\n        .summary-item p {\n            font-size: 24px;\n            font-weight: bold;\n            margin: 10px 0;\n        }\n        .summary-item.green p {\n            color: #27ae60;\n        }\n        .summary-item.red p {\n            color: #e74c3c;\n        }\n        .summary-item.yellow p {\n            color: #f39c12;\n        }\n        .summary-item.blue p {\n            color: #3498db;\n        }\n        table {\n            width: 100%;\n            border-collapse: collapse;\n            margin-bottom: 20px;\n        }\n        th, td {\n            padding: 12px 15px;\n            text-align: left;\n            border-bottom: 1px solid #ddd;\n        }\n        th {\n            background-color: #f2f2f2;\n            font-weight: bold;\n        }\n        tr:hover {\n            background-color: #f5f5f5;\n        }\n        .status-compliant {\n            color: #27ae60;\n            font-weight: bold;\n        }\n        .status-non-compliant {\n            color: #e74c3c;\n            font-weight: bold;\n        }\n        .status-not-applicable {\n            color: #7f8c8d;\n            font-style: italic;\n        }\n        .chart {\n            margin: 20px 0;\n            text-align: center;\n        }\n        .chart img {\n            max-width: 100%;\n            height: auto;\n        }\n        .footer {\n            text-align: center;\n            margin-top: 50px;\n            padding-top: 20px;\n            border-top: 1px solid #ddd;\n            color: #7f8c8d;\n        }\n        .finding {\n            background-color: #fff;\n            border-left: 4px solid #e74c3c;\n            padding: 15px;\n            margin-bottom: 15px;\n            box-shadow: 0 2px 5px rgba(0,0,0,0.1);\n        }\n        .finding h3 {\n            margin-top: 0;\n            color: #e74c3c;\n        }\n        .recommendation {\n            background-color: #fff;\n            border-left: 4px solid #3498db;\n            padding: 15px;\n            margin-bottom: 15px;\n            box-shadow: 0 2px 5px rgba(0,0,0,0.1);\n        }\n        .recommendation h3 {\n            margin-top: 0;\n            color: #3498db;\n        }\n        .priority-high {\n            color: #e74c3c;\n            font-weight: bold;\n        }\n        .priority-medium {\n            color: #f39c12;\n            font-weight: bold;\n        }\n        .priority-low {\n            color: #3498db;\n            font-weight: bold;\n        }\n        .evidence {\n            background-color: #f9f9f9;\n            padding: 15px;\n            margin-top: 10px;\n            border-radius: 5px;\n            font-family: monospace;\n            white-space: pre-wrap;\n            overflow-x: auto;\n        }\n        @media print {\n            .container {\n                max-width: 100%;\n                padding: 10px;\n            }\n            .section {\n                page-break-inside: avoid;\n            }\n            .no-break {\n                page-break-inside: avoid;\n            }\n        }\n    </style>\n</head>\n<body>\n    <div class="container">\n        <div class="header">\n            {% if organization.name %}\n            <h1>{{ organization.name }}</h1>\n            {% else %}\n            <h1>Nexora Healthcare</h1>\n            {% endif %}\n            <h2>{{ report.metadata.report_type|upper }} Compliance Report</h2>\n            <p>Period: {{ report.summary.period_start }} to {{ report.summary.period_end }}</p>\n            <p>Generated: {{ report.metadata.generated_at }}</p>\n        </div>\n\n        <div class="section">\n            <h2>Executive Summary</h2>\n            <div class="summary-box">\n                <div class="summary-item {% if report.summary.overall_compliance_percentage >= 90 %}green{% elif report.summary.overall_compliance_percentage >= 70 %}yellow{% else %}red{% endif %}">\n                    <h3>Overall Compliance</h3>\n                    <p>{{ "%.1f"|format(report.summary.overall_compliance_percentage) }}%</p>\n                    <span>{{ report.summary.compliance_status_text }}</span>\n                </div>\n                <div class="summary-item blue">\n                    <h3>Controls Assessed</h3>\n                    <p>{{ report.summary.total_applicable_controls }}</p>\n                    <span>Across {{ report.summary.standards|length }} standards</span>\n                </div>\n                <div class="summary-item green">\n                    <h3>Compliant Controls</h3>\n                    <p>{{ report.summary.compliant_controls }}</p>\n                    <span>{{ "%.1f"|format(report.summary.compliant_controls / report.summary.total_applicable_controls * 100) }}% of applicable controls</span>\n                </div>\n                <div class="summary-item red">\n                    <h3>Non-Compliant Controls</h3>\n                    <p>{{ report.summary.non_compliant_controls }}</p>\n                    <span>Requiring remediation</span>\n                </div>\n            </div>\n\n            {% if charts.compliance_by_standard %}\n            <div class="chart">\n                <h3>Compliance by Standard</h3>\n                <img src="{{ charts.compliance_by_standard }}" alt="Compliance by Standard">\n            </div>\n            {% endif %}\n\n            <h3>Standards Summary</h3>\n            <table>\n                <thead>\n                    <tr>\n                        <th>Standard</th>\n                        <th>Compliance</th>\n                        <th>Compliant Controls</th>\n                        <th>Non-Compliant Controls</th>\n                    </tr>\n                </thead>\n                <tbody>\n                    {% for standard_id, standard in report.summary.standards.items() %}\n                    <tr>\n                        <td>{{ standard.name }}</td>\n                        <td>{{ "%.1f"|format(standard.compliance_percentage) }}%</td>\n                        <td>{{ standard.compliant_controls }}</td>\n                        <td>{{ standard.non_compliant_controls }}</td>\n                    </tr>\n                    {% endfor %}\n                </tbody>\n            </table>\n        </div>\n\n        {% if report.findings %}\n        <div class="section">\n            <h2>Key Findings</h2>\n            <p>The following {{ report.findings|length }} findings require attention:</p>\n\n            {% for finding in report.findings %}\n            <div class="finding no-break">\n                <h3>{{ finding.control_title }}</h3>\n                <p><strong>Severity:</strong> <span class="priority-{{ finding.severity }}">{{ finding.severity|upper }}</span></p>\n                <p><strong>Standard:</strong> {{ finding.standard|upper }}</p>\n                <p><strong>Requirement:</strong> {{ finding.requirement_title }}</p>\n                <p><strong>Description:</strong> {{ finding.description }}</p>\n                <p><strong>Details:</strong> {{ finding.details }}</p>\n            </div>\n            {% endfor %}\n        </div>\n        {% endif %}\n\n        {% if report.recommendations %}\n        <div class="section">\n            <h2>Recommendations</h2>\n            <p>The following recommendations address the identified findings:</p>\n\n            {% for recommendation in report.recommendations %}\n            <div class="recommendation no-break">\n                <h3>{{ recommendation.title }}</h3>\n                <p><strong>Priority:</strong> <span class="priority-{{ recommendation.priority }}">{{ recommendation.priority|upper }}</span></p>\n                <p>{{ recommendation.description }}</p>\n            </div>\n            {% endfor %}\n        </div>\n        {% endif %}\n\n        {% for standard_id, standard_data in report.compliance_status.items() %}\n        <div class="section">\n            <h2>{{ standard_id|upper }} Compliance Details</h2>\n            <p>Overall compliance: {{ "%.1f"|format(standard_data.compliance_percentage) }}%</p>\n\n            {% if charts.get(standard_id + \'_compliance\') %}\n            <div class="chart">\n                <img src="{{ charts[standard_id + \'_compliance\'] }}" alt="{{ standard_id|upper }} Compliance">\n            </div>\n            {% endif %}\n\n            {% for req_id, req_data in standard_data.requirements.items() %}\n            <div class="no-break">\n                <h3>{{ req_data.title }}</h3>\n                <p>{{ req_data.description }}</p>\n                <p>Compliance: {{ "%.1f"|format(req_data.compliance_percentage) }}%</p>\n\n                <table>\n                    <thead>\n                        <tr>\n                            <th>Control</th>\n                            <th>Description</th>\n                            <th>Status</th>\n                        </tr>\n                    </thead>\n                    <tbody>\n                        {% for control_id, control in req_data.controls.items() %}\n                        <tr>\n                            <td>{{ control.title }}</td>\n                            <td>{{ control.description }}</td>\n                            <td class="status-{{ control.status }}">{{ control.status|replace(\'_\', \' \')|title }}</td>\n                        </tr>\n                        {% endfor %}\n                    </tbody>\n                </table>\n            </div>\n            {% endfor %}\n        </div>\n        {% endfor %}\n\n        {% if report.evidence and report.evidence|length > 0 %}\n        <div class="section">\n            <h2>Evidence</h2>\n            {% for evidence in report.evidence %}\n            <div class="no-break">\n                <h3>Evidence for {{ evidence.control_id }}</h3>\n                <p><strong>Type:</strong> {{ evidence.type }}</p>\n                <div class="evidence">{{ evidence.content }}</div>\n            </div>\n            {% endfor %}\n        </div>\n        {% endif %}\n\n        <div class="footer">\n            <p>Report ID: {{ report.metadata.report_id }}</p>\n            <p>Generated on {{ report.metadata.generated_at }}</p>\n            {% if organization.contact_email %}\n            <p>Contact: {{ organization.contact_email }}</p>\n            {% endif %}\n        </div>\n    </div>\n</body>\n</html>\n        '
        return jinja2.Template(template_str)

    def _generate_charts(self) -> Dict[str, str]:
        """
        Generate charts for the report

        Returns:
            Dictionary mapping chart name to file path
        """
        charts = {}
        charts_dir = os.path.join(self.output_dir, "charts")
        os.makedirs(charts_dir, exist_ok=True)
        standards = []
        compliance_values = []
        for standard_id, standard in self.report_data["summary"]["standards"].items():
            standards.append(standard["name"])
            compliance_values.append(standard["compliance_percentage"])
        if standards and compliance_values:
            plt.figure(figsize=(10, 6))
            bars = plt.bar(
                standards,
                compliance_values,
                color=[
                    "#27ae60" if v >= 90 else "#f39c12" if v >= 70 else "#e74c3c"
                    for v in compliance_values
                ],
            )
            plt.axhline(y=90, color="#27ae60", linestyle="--", alpha=0.7)
            plt.axhline(y=70, color="#f39c12", linestyle="--", alpha=0.7)
            for bar in bars:
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 1,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                )
            plt.ylim(0, 105)
            plt.title("Compliance by Standard")
            plt.ylabel("Compliance Percentage")
            plt.tight_layout()
            chart_path = os.path.join(charts_dir, "compliance_by_standard.png")
            plt.savefig(chart_path)
            plt.close()
            charts["compliance_by_standard"] = chart_path
        for standard_id, standard_data in self.report_data["compliance_status"].items():
            labels = ["Compliant", "Non-Compliant", "Not Applicable"]
            sizes = [
                standard_data["compliant_controls"],
                standard_data["non_compliant_controls"],
                standard_data["not_applicable_controls"],
            ]
            if sum(sizes) == 0:
                continue
            colors = ["#27ae60", "#e74c3c", "#95a5a6"]
            explode = (0.1, 0.1, 0)
            plt.figure(figsize=(8, 8))
            plt.pie(
                sizes,
                explode=explode,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                shadow=True,
                startangle=90,
            )
            plt.axis("equal")
            plt.title(f"{standard_id.upper()} Compliance Status")
            plt.tight_layout()
            chart_path = os.path.join(charts_dir, f"{standard_id}_compliance.png")
            plt.savefig(chart_path)
            plt.close()
            charts[f"{standard_id}_compliance"] = chart_path
        return charts

    def _anonymize_data(self, data: Dict) -> Dict:
        """
        Anonymize sensitive data in the report

        Args:
            data: Report data to anonymize

        Returns:
            Anonymized report data
        """
        import copy

        anonymized = copy.deepcopy(data)
        if "evidence" in anonymized:
            for evidence in anonymized["evidence"]:
                if "content" in evidence:
                    evidence["content"] = re.sub(
                        "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b",
                        "xxx.xxx.xxx.xxx",
                        evidence["content"],
                    )
                    evidence["content"] = re.sub(
                        "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
                        "xxx@example.com",
                        evidence["content"],
                    )
                    evidence["content"] = re.sub(
                        "user[:\\s]+\\w+", "user: xxxxx", evidence["content"]
                    )
                    evidence["content"] = re.sub(
                        "patient[_\\-\\s]?id[:\\s]+\\w+",
                        "patient_id: xxxxx",
                        evidence["content"],
                    )
        return anonymized


def parse_args() -> Any:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Automated Compliance Report Generator for Nexora",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1],
    )
    parser.add_argument(
        "--config",
        default="config/compliance_config.yaml",
        help="Path to config file (default: config/compliance_config.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        default="./compliance_reports",
        help="Directory to save reports (default: ./compliance_reports)",
    )
    parser.add_argument(
        "--report-type",
        choices=["hipaa", "gdpr", "hitech", "all"],
        default="all",
        help="Type of report to generate (hipaa, gdpr, hitech, all) (default: all)",
    )
    parser.add_argument(
        "--period",
        choices=["day", "week", "month", "quarter", "year"],
        default="month",
        help="Time period to analyze (day, week, month, quarter, year) (default: month)",
    )
    parser.add_argument(
        "--end-date", help="End date for analysis in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "html", "json", "all"],
        default="pdf",
        help="Output format (pdf, html, json, all) (default: pdf)",
    )
    parser.add_argument(
        "--include-evidence",
        action="store_true",
        help="Include evidence files in report",
    )
    parser.add_argument(
        "--anonymize", action="store_true", help="Anonymize sensitive data in reports"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    return parser.parse_args()


def main() -> Any:
    """Main entry point"""
    args = parse_args()
    try:
        formats = []
        if args.format == "all":
            formats = ["pdf", "html", "json"]
        else:
            formats = [args.format]
        generator = ComplianceReportGenerator(
            config_path=args.config,
            output_dir=args.output_dir,
            report_type=args.report_type,
            period=args.period,
            end_date=args.end_date,
            include_evidence=args.include_evidence,
            anonymize=args.anonymize,
            verbose=args.verbose,
        )
        output_files = generator.generate_reports(formats=formats)
        logger.info("Generated reports:")
        for format_type, file_path in output_files.items():
            if file_path:
                logger.info(f"  {format_type.upper()}: {file_path}")
        return 0
    except Exception as e:
        logger.error(f"Error generating compliance reports: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
