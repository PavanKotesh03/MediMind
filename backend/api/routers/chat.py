from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import logging
import json
import asyncio

from api.schemas.chat import StartRequest, ResetRequest
from api.schemas.response import APIResponse
from services.chat_service import start_session, chat_session_streaming, reset_session
from guardrails.guard_exceptions import PromptInjectionError
from auth.jwt_bearer import JWTBearer
from auth.jwt_handler import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


@router.post("/start", response_model=None)
def start_chat(
    req: StartRequest,
    user_email: str = Depends(JWTBearer()),
):
    """
    Create new empty chat session
    Called by: Login and "New Chat" button
    """
    try:
        session_id, reply, finished = start_session(req.message, user_email)

        return APIResponse(
            success=True,
            message="Chat session started",
            data={
                "session_id": session_id,
                "finished": finished,
                "reply": reply,
            },
        )

    except PromptInjectionError as e:
        return APIResponse(
            success=False,
            message="Unsafe input detected",
            error=str(e),
        )


@router.get("/chat/stream")
async def stream_chat_response(
    session_id: str = Query(..., description="Chat session ID"),
    message: str = Query(..., description="User message"),
    token: str = Query(..., description="JWT authentication token"),
):
    """
    Stream LLM response word-by-word using Server-Sent Events
    - Handles FIRST message and ALL subsequent messages
    - Saves messages to database during streaming
    - Token passed as query param (EventSource doesn't support headers)
    """
    
    try:
        user_email = verify_token(token)
        logger.info(f"Streaming authenticated for user: {user_email}, session: {session_id}")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        
        async def error_generator():
            error_data = {
                "error": "Unauthorized - invalid or expired token",
                "type": "error"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    async def event_generator():
        try:
            logger.info(f"Starting stream for session {session_id}")
            
            # Use streaming generator - handles DB saving automatically
            for chunk in chat_session_streaming(session_id, message):
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)
            
            yield f"data: [DONE]\n\n"
            logger.info(f"Stream completed for {session_id}")
            
        except PromptInjectionError as e:
            logger.warning(f"Prompt injection detected: {e}")
            error_data = {
                "error": "Unsafe input detected",
                "type": "error"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error for {session_id}: {e}", exc_info=True)
            error_data = {
                "error": str(e),
                "type": "error"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("/reset", response_model=None)
def reset(
    req: ResetRequest,
    user_email: str = Depends(JWTBearer()),
):
    reset_session(req.session_id)

    return APIResponse(
        success=True,
        message="Session reset successfully",
        data={"session_id": req.session_id},
    )
