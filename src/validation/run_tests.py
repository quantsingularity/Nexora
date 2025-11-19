"""
Test runner script for the HIPAA-compliant readmission prediction pipeline.

This script runs all tests for the pipeline and generates a comprehensive report.
"""

import json
import logging
import os
import sys
import unittest
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def run_tests(output_dir="test_results"):
    """
    Run all tests for the HIPAA-compliant readmission prediction pipeline.

    Args:
        output_dir: Directory for test results

    Returns:
        Dictionary containing test results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "tests")
    suite = loader.discover(start_dir, pattern="test_*.py")

    # Run tests and capture results
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate test report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "success": result.wasSuccessful(),
        "details": {
            "failures": [
                {"test": test, "message": message} for test, message in result.failures
            ],
            "errors": [
                {"test": test, "message": message} for test, message in result.errors
            ],
            "skipped": [
                {"test": test, "message": message} for test, message in result.skipped
            ],
        },
    }

    # Save report to file
    report_path = os.path.join(output_dir, "test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Test report saved to {report_path}")

    # Generate summary
    summary = f"""
    ======================================
    HIPAA Compliance Test Results Summary
    ======================================

    Tests Run: {report['total_tests']}
    Failures: {report['failures']}
    Errors: {report['errors']}
    Skipped: {report['skipped']}

    Overall Status: {'PASS' if report['success'] else 'FAIL'}

    Timestamp: {report['timestamp']}

    See {report_path} for detailed results.
    """

    # Save summary to file
    summary_path = os.path.join(output_dir, "test_summary.txt")
    with open(summary_path, "w") as f:
        f.write(summary)

    logger.info(f"Test summary saved to {summary_path}")
    logger.info(summary)

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run tests for HIPAA-compliant readmission prediction pipeline"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_results",
        help="Directory for test results",
    )

    args = parser.parse_args()

    run_tests(output_dir=args.output_dir)
