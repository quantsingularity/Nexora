from openlineage.client import OpenLineageClient
from openlineage.facet import DataQualityMetrics


class ClinicalLineageTracker:
    def __init__(self):
        self.client = OpenLineageClient(url="http://marquez:5000")

    def log_pipeline_run(self, dataset, model_version):
        lineage_event = {
            "eventType": "START",
            "eventTime": datetime.now().isoformat(),
            "run": {
                "runId": str(uuid.uuid4()),
                "facets": {
                    "dataQuality": DataQualityMetrics(
                        rowCount=dataset.shape[0],
                        columnCount=dataset.shape[1],
                        nullCount=dataset.isnull().sum().to_dict(),
                    )
                },
            },
            "inputs": [
                {
                    "name": "source_fhir_server",
                    "facets": {
                        "dataSource": {"uri": "fhir://cms.gov/"},
                        "schema": {
                            "fields": [
                                {"name": col, "type": str(dtype)}
                                for col, dtype in dataset.dtypes.items()
                            ]
                        },
                    },
                }
            ],
            "outputs": [
                {
                    "name": "readmission_predictions",
                    "facets": {
                        "model": {
                            "name": "readmission_risk_v2",
                            "version": model_version,
                        }
                    },
                }
            ],
        }
        self.client.emit(lineage_event)
