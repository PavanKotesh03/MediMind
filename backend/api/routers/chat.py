from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import logging
import json
import asyncio

from api.schemas.chat import StartRequest, ChatRequest, ResetRequest
from api.schemas.response import APIResponse
from services.chat_service import start_session, chat_session, reset_session
from guardrails.guard_exceptions import PromptInjectionError
from auth.jwt_bearer import JWTBearer
from auth.jwt_handler import verify_token  # ✅ Import token verifier


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


# =====================================================
# START INTERVIEW
# =====================================================
@router.post("/start", response_model=None)
def start_chat(
    req: StartRequest,
    user_email: str = Depends(JWTBearer()),
):
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


# =====================================================
# CHAT CONTINUATION
# =====================================================
@router.post("/chat", response_model=None)
def chat(
    req: ChatRequest,
    user_email: str = Depends(JWTBearer()),
):
    result = chat_session(req.session_id, req.message)

    if result["finished"]:
        return APIResponse(
            success=True,
            message="Chat completed",
            data={
                "session_id": req.session_id,
                "finished": True,
                "final": result["final"],
            },
        )

    return APIResponse(
        success=True,
        message="Next question generated",
        data={
            "session_id": req.session_id,
            "finished": False,
            "reply": result["reply"],
        },
    )


# =====================================================
# 🆕 STREAMING CHAT ENDPOINT
# =====================================================
@router.get("/chat/stream")
async def stream_chat_response(
    session_id: str = Query(..., description="Chat session ID"),
    message: str = Query(..., description="User message"),
    token: str = Query(..., description="JWT authentication token"),  # ✅ Token as query param
):
    """
    Stream LLM response word-by-word using Server-Sent Events (SSE)
    
    Token is passed as query param because EventSource doesn't support custom headers
    
    Returns:
        StreamingResponse with SSE format:
        - data: {"content": "word", "finished": false, "type": "text"}
        - data: {"finished": true, "final": {...}, "type": "final"}
        - data: [DONE] when complete
    """
    
    # ✅ Manually verify JWT token
    try:
        user_email = verify_token(token)
        logger.info(f"✅ Streaming authenticated for user: {user_email}, session: {session_id}")
    except Exception as e:
        logger.error(f"❌ Token verification failed: {e}")
        
        # Return error event
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
                "Connection": "keep-alive"
            }
        )
    
    # ✅ Token verified - proceed with streaming
    async def event_generator():
        try:
            logger.info(f"🌊 Starting stream for session {session_id}")
            
            # Get the full response from chat_session
            result = chat_session(session_id, message)
            
            if result["finished"]:
                # Stream final assessment
                final_data = result.get("final", {})
                explanation = final_data.get("explanation", "Assessment complete.")
                
                logger.info(f"📋 Streaming final assessment for {session_id}")
                
                # Stream explanation word by word
                words = explanation.split()
                for i, word in enumerate(words):
                    chunk = {
                        "content": word + (" " if i < len(words) - 1 else ""),
                        "finished": False,
                        "type": "text"
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.03)  # 30ms delay between words
                
                # Send final assessment data
                final_chunk = {
                    "content": "",
                    "finished": True,
                    "final": final_data,
                    "type": "final"
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                logger.info(f"✅ Final assessment streamed for {session_id}")
                
            else:
                # Stream regular reply word by word
                reply = result.get("reply", "")
                words = reply.split()
                
                logger.info(f"💬 Streaming reply: {len(words)} words")
                
                for i, word in enumerate(words):
                    chunk = {
                        "content": word + (" " if i < len(words) - 1 else ""),
                        "finished": False,
                        "type": "text"
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.03)  # 30ms delay
                
                logger.info(f"✅ Reply streamed for {session_id}")
            
            # Send completion signal
            yield f"data: [DONE]\n\n"
            logger.info(f"🏁 Stream completed for {session_id}")
            
        except PromptInjectionError as e:
            logger.warning(f"⚠️ Prompt injection detected: {e}")
            error_data = {
                "error": "Unsafe input detected",
                "type": "error"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ Streaming error for {session_id}: {e}", exc_info=True)
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
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# =====================================================
# RESET CHAT
# =====================================================
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
