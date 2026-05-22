import logging
from fastapi import APIRouter, Depends
from app.core.config import Settings, get_settings
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health Check", tags=["System"])
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    logger.debug("Health check requested")
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
        message=f"{settings.app_name} is running",
    )
