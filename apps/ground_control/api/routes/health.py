from fastapi import APIRouter
from ..schemas import HealthResponse
from luna_ai import __version__

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Service liveness check."""
    return HealthResponse(status="ok", version=__version__)
