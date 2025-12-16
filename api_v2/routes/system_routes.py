"""
System routes for the Medical Interview Chatbot API V2.
Defines system-level endpoints like health checks and root info.
"""

from fastapi import APIRouter
from api_v2.models.schemas import HealthResponse, RootResponse

# Create router for system endpoints
router = APIRouter(tags=["system"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy", 
        message="Medical Interview Chatbot API V2 is running"
    )

@router.get("/", response_model=RootResponse)
async def root():
    """Root endpoint with API information."""
    return RootResponse(
        message="Welcome to the Medical Interview Chatbot API V2", 
        docs="/docs",
        endpoints={
            "POST /api/v2/chat/start": "Start a new medical interview",
            "POST /api/v2/chat": "Continue an existing medical interview (renamed from /reply)",
            "POST /api/v2/chat/reset": "Reset a medical interview session",
            "GET /health": "Health check"
        }
    )