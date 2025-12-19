from fastapi import APIRouter, HTTPException
from guardrails.guard_exceptions import PromptInjectionError

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

router = APIRouter(tags=["Chat"])


# =====================================================
# START INTERVIEW
# =====================================================
@router.post("/start", response_model=ChatResponse)
def start_chat(req: StartRequest):
    try:
        session_id, reply, finished = start_session(req.message)
    except PromptInjectionError as e:
        # 🔒 Guardrail violation → client error
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return ChatResponse(
        session_id=session_id,
        finished=finished,
        reply=reply
    )


# =====================================================
# CHAT (INTERVIEW CONTINUATION)
# =====================================================
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        result = chat_session(req.session_id, req.message)

    except PromptInjectionError as e:
        # 🔒 Guardrail violation
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except ValueError as e:
        # Invalid session_id etc.
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # 🔚 Interview finished → return FINAL explanation
    if result["finished"]:
        return ChatResponse(
            session_id=req.session_id,
            finished=True,
            final=result["final"]
        )

    # 🟢 Continue interview → return next question
    return ChatResponse(
        session_id=req.session_id,
        finished=False,
        reply=result["reply"]
    )


# =====================================================
# RESET SESSION
# =====================================================
@router.post("/reset")
def reset(req: ResetRequest):
    reset_session(req.session_id)
    return {"status": "session reset"}
