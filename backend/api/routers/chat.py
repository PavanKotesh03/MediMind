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
