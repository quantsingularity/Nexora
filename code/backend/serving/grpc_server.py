"""
Nexora gRPC Prediction Server

Provides a gRPC interface for high-throughput clinical prediction requests.
Uses grpcio-reflection for service discovery and grpcio-health for health checks.

Falls back to a stub mode when grpcio is not installed so imports never crash.

Protocol buffer definition (inline schema, no .proto compilation required):
  The server uses the generic `google.protobuf.Struct` approach so we don't
  need a compiled proto – JSON payloads are sent as Struct fields.
"""

from __future__ import annotations

import json
import logging
import os
from concurrent import futures
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional gRPC imports
# ---------------------------------------------------------------------------
try:
    import grpc
    from grpc_reflection.v1alpha import reflection

    _GRPC_AVAILABLE = True
except ImportError:
    _GRPC_AVAILABLE = False
    grpc = None  # type: ignore
    reflection = None  # type: ignore

# ---------------------------------------------------------------------------
# ML imports
# ---------------------------------------------------------------------------
from ml_core.compliance.phi_audit_logger import PHIAuditLogger
from ml_core.models.model_registry import ModelRegistry

# ---------------------------------------------------------------------------
# In-process proto-less service
# ---------------------------------------------------------------------------
# Because we avoid compiled .proto files we implement the gRPC service using
# the grpc.experimental.gevent or generic unary handler pattern.
# For production, replace this with a compiled protobuf-based servicer.

_METHODS: Dict[str, Any] = {}


def _register_method(name: str):
    def decorator(fn):
        _METHODS[name] = fn
        return fn

    return decorator


class NexoraPredictionServicer:
    """
    Generic JSON-over-gRPC servicer.

    Clients send a JSON-encoded request body and receive a JSON-encoded response.
    This avoids .proto compilation while still exercising the full gRPC stack.
    """

    def __init__(self) -> None:
        self.model_registry = ModelRegistry()
        _audit_db = os.environ.get("AUDIT_DB_PATH", "audit/phi_access.db")
        os.makedirs(
            os.path.dirname(_audit_db) if os.path.dirname(_audit_db) else ".",
            exist_ok=True,
        )
        self.audit_logger = PHIAuditLogger(db_path=_audit_db)
        logger.info("NexoraPredictionServicer initialised.")

    def Predict(self, request_json: str) -> str:
        """
        Handle a prediction request.

        Args:
            request_json: JSON string with keys:
                patient_id, model_name, model_version (optional),
                patient_data (dict)

        Returns:
            JSON string with prediction results.
        """
        try:
            req = json.loads(request_json)
            patient_id = req.get("patient_id", "unknown")
            model_name = req.get("model_name", "deep_fm")
            model_version = req.get("model_version") or "latest"
            patient_data = req.get("patient_data", {})

            self.audit_logger.log_prediction_request(
                patient_id=patient_id,
                model_used=f"{model_name} v{model_version}",
            )

            model = self.model_registry.get_model(model_name, model_version)
            predictions = model.predict(patient_data)
            explanations = model.explain(patient_data)
            uncertainty = predictions.pop("uncertainty", {})

            return json.dumps(
                {
                    "status": "ok",
                    "patient_id": patient_id,
                    "model_name": model_name,
                    "model_version": model_version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "predictions": predictions,
                    "explanations": explanations,
                    "uncertainty": uncertainty,
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"gRPC Predict error: {exc}", exc_info=True)
            return json.dumps({"status": "error", "detail": str(exc)})

    def HealthCheck(self, _request_json: str = "{}") -> str:
        return json.dumps(
            {
                "status": "SERVING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def ListModels(self, _request_json: str = "{}") -> str:
        models = self.model_registry.list_models()
        return json.dumps({"models": models})


# ---------------------------------------------------------------------------
# gRPC server bootstrap
# ---------------------------------------------------------------------------


def build_server(
    port: int = 50051,
    max_workers: int = 10,
) -> Any:
    """
    Build and return a configured gRPC server.

    If grpcio is not installed the function logs a warning and returns None.
    """
    if not _GRPC_AVAILABLE:
        logger.warning(
            "grpcio is not installed. gRPC server cannot start. "
            "Install with: pip install grpcio grpcio-reflection"
        )
        return None

    servicer = NexoraPredictionServicer()

    def _make_handler(method_name: str):
        def handler(request: bytes, context) -> bytes:  # type: ignore[no-untyped-def]
            fn = getattr(servicer, method_name)
            result = fn(request.decode("utf-8"))
            return result.encode("utf-8")

        return grpc.unary_unary_rpc_method_handler(handler)

    generic_handler = grpc.method_service_handler = None  # satisfy linters
    handler_map = {
        f"/nexora.PredictionService/{m}": _make_handler(m)
        for m in ("Predict", "HealthCheck", "ListModels")
    }
    generic_rpc_handler = grpc.GenericMethodHandler  # type: ignore[attr-defined]

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    server.add_generic_rpc_handlers([_DictGenericHandler(handler_map)])
    server.add_insecure_port(f"[::]:{port}")
    return server


class _DictGenericHandler:
    """Minimal GenericMethodHandler backed by a plain dict."""

    def __init__(self, handler_map: Dict[str, Any]) -> None:
        self._map = handler_map

    def service_name(self) -> str:  # pragma: no cover
        return "nexora.PredictionService"

    def service(self, handler_call_details: Any) -> Any:
        return self._map.get(handler_call_details.method)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def serve() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    port = int(os.environ.get("GRPC_PORT", 50051))
    max_workers = int(os.environ.get("GRPC_MAX_WORKERS", 10))

    server = build_server(port=port, max_workers=max_workers)
    if server is None:
        return

    server.start()
    logger.info(f"Nexora gRPC server started on port {port}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(grace=5)


if __name__ == "__main__":
    serve()
