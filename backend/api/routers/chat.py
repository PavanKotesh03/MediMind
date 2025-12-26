from fastapi import APIRouter, HTTPException, Depends
from api.schemas.chat import (
    StartRequest,
    ChatRequest,
    ChatResponse,
    ResetRequest
)
from services.chat_service import (
    start_session,
    chat_session,
    reset_session
)
from guardrails.guard_exceptions import PromptInjectionError
from auth.jwt_bearer import JWTBearer  # NEW IMPORT


router = APIRouter(tags=["Chat"])



# =====================================================
# START INTERVIEW (JWT PROTECTED)
# =====================================================
@router.post("/start", response_model=ChatResponse)
def start_chat(req: StartRequest, user_email: str = Depends(JWTBearer())):  # CHANGED
    """
    Start a new medical interview chat session.
    
    - **message**: First user message (symptoms)
    - JWT token required in Authorization header
    """
    try:
        # Use user_email from JWT token (not from request)
        session_id, reply, finished = start_session(req.message, user_email)  # CHANGED
        
        return ChatResponse(
            session_id=session_id,
            finished=finished,
            reply=reply
        )
        
    except PromptInjectionError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting chat: {str(e)}"
        )



# =====================================================
# CHAT (INTERVIEW CONTINUATION - JWT PROTECTED)
# =====================================================
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user_email: str = Depends(JWTBearer())):  # CHANGED
    """
    Continue an existing chat session.
    
    - **session_id**: UUID of the active session
    - **message**: User's response to bot's question
    - JWT token required in Authorization header
    """
    try:
        result = chat_session(req.session_id, req.message)
        
        if result["finished"]:
            return ChatResponse(
                session_id=req.session_id,
                finished=True,
                final=result["final"]
            )
        
        return ChatResponse(
            session_id=req.session_id,
            finished=False,
            reply=result["reply"]
        )
        
    except PromptInjectionError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat: {str(e)}"
        )




# RESET SESSION (JWT PROTECTED)
@router.post("/reset")
def reset(req: ResetRequest, user_email: str = Depends(JWTBearer())):  # CHANGED
    """
    Reset/clear a chat session from memory.
    
    - **session_id**: UUID of session to reset
    - JWT token required in Authorization header
    """
    try:
        reset_session(req.session_id)
        return {
            "status": "session reset",
            "session_id": req.session_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting session: {str(e)}"
        )
