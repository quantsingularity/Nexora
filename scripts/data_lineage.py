"""
Clinical data lineage tracking via OpenLineage.

Emits a START run event for a readmission-prediction pipeline run, tagging
it with basic data-quality metrics (row/column counts, null counts) and
schema information about the source dataset.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from openlineage.client import OpenLineageClient
from openlineage.client.facet import (
    DataQualityMetricsInputDatasetFacet,
    SchemaDatasetFacet,
    SchemaField,
)
from openlineage.client.run import Dataset, Job, Run, RunEvent, RunState

NAMESPACE = "nexora.clinical"
JOB_NAME = "readmission_risk_pipeline"


class ClinicalLineageTracker:
    """Tracks lineage of the readmission-risk training/scoring pipeline."""

    def __init__(self, marquez_url: str = "http://marquez:5000") -> None:
        self.client = OpenLineageClient(url=marquez_url)

    def log_pipeline_run(self, dataset: Any, model_version: str) -> str:
        """Emit a lineage START event for a pipeline run over `dataset`.

        Returns the generated run ID so callers can later emit a matching
        COMPLETE/FAIL event for the same run.
        """
        run_id = str(uuid.uuid4())

        input_dataset = Dataset(
            namespace="fhir",
            name="source_fhir_server",
            facets={
                "dataQualityMetrics": DataQualityMetricsInputDatasetFacet(
                    rowCount=int(dataset.shape[0]),
                    columnCount=int(dataset.shape[1]),
                    nullCount=dataset.isnull().sum().to_dict(),
                ),
                "schema": SchemaDatasetFacet(
                    fields=[
                        SchemaField(name=col, type=str(dtype))
                        for col, dtype in dataset.dtypes.items()
                    ]
                ),
            },
        )

        output_dataset = Dataset(
            namespace=NAMESPACE,
            name="readmission_predictions",
            facets={
                "model": {
                    "name": "readmission_risk_v2",
                    "version": model_version,
                }
            },
        )

        event = RunEvent(
            eventType=RunState.START,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=Run(runId=run_id),
            job=Job(namespace=NAMESPACE, name=JOB_NAME),
            producer="https://github.com/quantsingularity/Nexora",
            inputs=[input_dataset],
            outputs=[output_dataset],
        )

        self.client.emit(event)
        return run_id

    def log_pipeline_complete(self, run_id: str) -> None:
        """Emit a matching COMPLETE event for a run started by
        `log_pipeline_run`."""
        event = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=Run(runId=run_id),
            job=Job(namespace=NAMESPACE, name=JOB_NAME),
            producer="https://github.com/quantsingularity/Nexora",
            inputs=[],
            outputs=[],
        )
        self.client.emit(event)
