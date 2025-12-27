"""
gRPC Server Module for Nexora

This module provides a gRPC server for high-performance model serving.
It implements prediction services with proper error handling and logging.
"""

import logging
import os
from concurrent import futures
from typing import Any, Dict

import grpc

from model_factory.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ClinicalDataError(Exception):
    """Exception raised for errors in clinical data processing."""


class PredictionService:
    """
    gRPC service implementation for clinical prediction.

    This service provides prediction endpoints for clinical models using gRPC protocol.
    """

    def __init__(self):
        """Initialize the prediction service with model registry."""
        self.model_registry = ModelRegistry()
        logger.info("Initialized PredictionService with ModelRegistry")

    def Predict(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle prediction requests via gRPC.

        Args:
            request: Dictionary containing prediction request data with:
                - model_name: Name of the model to use
                - model_version: Version of the model (optional)
                - patient_data: Patient clinical data

        Returns:
            Dictionary containing prediction results with:
                - predictions: Model predictions
                - explanations: Prediction explanations
                - uncertainty: Uncertainty estimates

        Raises:
            ClinicalDataError: If the input data is invalid
            Exception: For other errors during prediction
        """
        try:
            # Extract request parameters
            model_name = request.get("model_name", "deep_fm")
            model_version = request.get("model_version", "latest")
            patient_data = request.get("patient_data", {})

            # Validate input
            if not patient_data:
                raise ClinicalDataError("Patient data is required for prediction")

            # Get model from registry
            model = self.model_registry.get_model(model_name, model_version)

            # Generate predictions
            predictions = model.predict(patient_data)

            # Generate explanations
            explanations = model.explain(patient_data)

            # Return response
            return {
                "predictions": predictions,
                "explanations": explanations,
                "model_name": model_name,
                "model_version": model_version,
            }

        except ClinicalDataError as e:
            logger.error(f"Clinical data error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise


def serve(port: int = 50051, max_workers: int = 10) -> None:
    """
    Start the gRPC server.

    Args:
        port: Port number to listen on (default: 50051)
        max_workers: Maximum number of concurrent workers (default: 10)
    """
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    # Add prediction service
    PredictionService()

    # Note: In a real implementation, you would register the service with:
    # prediction_service_pb2_grpc.add_PredictionServiceServicer_to_server(
    #     prediction_service, server
    # )
    # For now, we just log that the service is initialized
    logger.info(f"PredictionService initialized and ready to be registered")

    # Bind server to port
    server.add_insecure_port(f"[::]:{port}")

    # Start server
    server.start()
    logger.info(f"gRPC server started on port {port} with {max_workers} workers")

    # Wait for termination
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC server stopping...")
        server.stop(0)


if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.environ.get("GRPC_PORT", 50051))
    max_workers = int(os.environ.get("GRPC_MAX_WORKERS", 10))

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Start server
    serve(port=port, max_workers=max_workers)
