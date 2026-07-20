from backend.app.api.auth_routes import router as auth_router
from backend.app.api.dashboard_routes import router as dashboard_router
from backend.app.api.notification_routes import router as notification_router
from backend.app.api.patient_routes import router as patient_router
from backend.app.api.routes import router

__all__ = [
    "router",
    "auth_router",
    "patient_router",
    "dashboard_router",
    "notification_router",
]
