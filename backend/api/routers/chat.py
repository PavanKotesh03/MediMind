from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import logging
import json

from api.schemas.chat import StartRequest, ChatRequest, ResetRequest
from api.schemas.response import APIResponse
from services.chat_service import (
    start_session_streaming,
    chat_session_streaming,
    reset_session
)
from guardrails.guard_exceptions import PromptInjectionError
from auth.jwt_bearer import JWTBearer

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


# =====================================================
# START INTERVIEW (STREAMING ONLY)
# =====================================================
@router.post("/start")
async def start_chat(
    req: StartRequest,
    user_email: str = Depends(JWTBearer()),
):
    """
    Start chat with streaming response
    Returns Server-Sent Events (SSE)
    """
    try:
        async def event_generator():
            try:
                async for chunk in start_session_streaming(req.message, user_email):
                    # Send as Server-Sent Event
                    yield f"data: {json.dumps(chunk)}\n\n"
            except PromptInjectionError as e:
                error_data = {
                    "type": "error",
                    "data": {
                        "message": "Unsafe input detected",
                        "error": str(e)
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = {
                    "type": "error",
                    "data": {
                        "message": "An error occurred",
                        "error": str(e)
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to start streaming: {e}")
        return APIResponse(
            success=False,
            message="Failed to start chat",
            error=str(e)
        )


# =====================================================
# CHAT CONTINUATION (STREAMING ONLY)
# =====================================================
@router.post("/chat")
async def chat(
    req: ChatRequest,
    user_email: str = Depends(JWTBearer()),
):
    """
    Continue chat with streaming response
    Returns Server-Sent Events (SSE)
    """
    try:
        async def event_generator():
            try:
                async for chunk in chat_session_streaming(req.session_id, req.message):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except PromptInjectionError as e:
                error_data = {
                    "type": "error",
                    "data": {
                        "message": "Unsafe input detected",
                        "error": str(e)
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            except ValueError as e:
                error_data = {
                    "type": "error",
                    "data": {
                        "message": str(e),
                        "error": str(e)
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            except Exception as e:
                logger.error(f"Streaming chat error: {e}")
                error_data = {
                    "type": "error",
                    "data": {
                        "message": "An error occurred",
                        "error": str(e)
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to start chat streaming: {e}")
        return APIResponse(
            success=False,
            message="Failed to process chat",
            error=str(e)
        )


# =====================================================
# RESET CHAT
# =====================================================
@router.post("/reset", response_model=None)
def reset(
    req: ResetRequest,
    user_email: str = Depends(JWTBearer()),
):
    """Reset chat session"""
    reset_session(req.session_id)
    
    return APIResponse(
        success=True,
        message="Session reset successfully",
        data={"session_id": req.session_id},
    )
