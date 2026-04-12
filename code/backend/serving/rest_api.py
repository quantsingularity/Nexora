"""
Nexora REST API entry point.

App creation and middleware setup lives here.
All route handlers are defined in backend.app.api.routes.
"""

from __future__ import annotations

import logging
import os

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    uvicorn = None  # type: ignore

if _FASTAPI_AVAILABLE:
    from backend.app.api.routes import router
    from backend.app.core.config import settings

    app = FastAPI(
        title=settings.APP_NAME,
        description="Clinical prediction and decision support API for Nexora",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "unknown")
        logger.info(f"→ {request.method} {request.url.path} [{request_id}]")
        response = await call_next(request)
        logger.info(f"← {response.status_code} [{request_id}]")
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    app.include_router(router)

    if __name__ == "__main__":
        uvicorn.run(
            "backend.serving.rest_api:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower(),
        )

else:
    logger.warning("FastAPI not available; REST API endpoints are inactive.")
    app = None  # type: ignore
