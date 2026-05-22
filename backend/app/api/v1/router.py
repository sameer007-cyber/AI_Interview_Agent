"""
Central API v1 router.
All endpoint routers are registered here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.interview import router as interview_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(interview_router)
