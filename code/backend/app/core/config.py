"""
Application configuration via environment variables.
"""

from __future__ import annotations

import os


class Settings:
    APP_NAME: str = "Nexora Clinical API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"

    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", 8000))

    AUDIT_DB_PATH: str = os.environ.get("AUDIT_DB_PATH", "audit/phi_access.db")
    APP_DB_PATH: str = os.environ.get("APP_DB_PATH", "data/nexora_app.db")
    FHIR_SERVER_URL: str = os.environ.get(
        "FHIR_SERVER_URL", "http://mock-fhir-server/R4"
    )
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    # Auth
    JWT_SECRET_KEY: str = os.environ.get(
        "JWT_SECRET_KEY", "dev-only-insecure-secret-change-me-in-production"
    )
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(
        os.environ.get("JWT_EXPIRE_MINUTES", str(60 * 24 * 7))  # 7 days
    )

    # CORS
    CORS_ORIGINS: list[str] = os.environ.get("CORS_ORIGINS", "*").split(",")

    # Feature store
    FEATURE_STORE_PATH: str = os.environ.get("FEATURE_STORE_PATH", "data/feature_store")

    # Artifact store
    ARTIFACT_STORE_PATH: str = os.environ.get("ARTIFACT_STORE_PATH", "artifacts")


settings = Settings()
