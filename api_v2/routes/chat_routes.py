"""
Chat routes for the Medical Interview Chatbot API V2.
Defines the API endpoints for chat interactions.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, ResetRequest
from services.chat_service import start_chat_session, continue_chat_session, reset_chat_session

# Create router for chat endpoints
router = APIRouter(prefix="/api/v2", tags=["chat"])

@router.post("/chat/start", response_model=ChatResponse)
async def start_chat(request: ChatRequest):
    """Start a new medical interview session."""
    try:
        response, finished, history = start_chat_session(request.session_id, request.message)
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            finished=finished,
            history=history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Continue an existing medical interview session (renamed from /reply)."""
    try:
        response, finished, history = continue_chat_session(request.session_id, request.message)
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            finished=finished,
            history=history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/reset")
async def reset_chat(request: ResetRequest):
    """Reset an existing medical interview session."""
    try:
        success = reset_chat_session(request.session_id)
        if success:
            return {"message": f"Session {request.session_id} has been reset"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reset session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))