from fastapi import APIRouter, HTTPException

from api.schemas.chat import (
    StartRequest,
    ChatRequest,
    ChatResponse,
    ResetRequest  # ADD THIS
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
    session_id, reply, finished = start_session(req.message)

    return ChatResponse(
        session_id=session_id,
        finished=finished,
        reply=reply
    )

# =====================================================
# CHAT (AUTO FINAL WHEN INTERVIEW ENDS)
# =====================================================
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        result = chat_session(req.session_id, req.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Interview finished → return FINAL explanation
    if result["finished"]:
        return ChatResponse(
            session_id=req.session_id,
            finished=True,
            final=result["final"]
        )

    # Continue interview → return next question
    return ChatResponse(
        session_id=req.session_id,
        finished=False,
        reply=result["reply"]
    )

# =====================================================
# RESET SESSION (UPDATED)
# =====================================================
@router.post("/reset")
def reset(req: ResetRequest):  # CHANGED FROM ChatRequest
    reset_session(req.session_id)
    return {"status": "session reset", "session_id": req.session_id}
