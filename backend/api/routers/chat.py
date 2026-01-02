# from fastapi import APIRouter, Depends
# import logging

# from api.schemas.chat import (
#     StartRequest,
#     ChatRequest,
#     ChatResponse,
#     ResetRequest
# )
# from api.schemas.response import APIResponse   # ✅ COMMON RESPONSE MODEL
# from services.chat_service import (
#     start_session,
#     chat_session,
#     reset_session
# )
# from guardrails.guard_exceptions import PromptInjectionError
# from auth.jwt_bearer import JWTBearer

# logger = logging.getLogger(__name__)

# router = APIRouter(tags=["Chat"])


# # =====================================================
# # START INTERVIEW (JWT PROTECTED)
# # =====================================================
# @router.post("/start", response_model=APIResponse[ChatResponse])
# def start_chat(req: StartRequest, user_email: str = Depends(JWTBearer())):
#     """
#     Start a new medical interview chat session.
#     """
#     logger.info(f"Starting new chat session for user: {user_email}")

#     try:
#         session_id, reply, finished = start_session(req.message, user_email)

#         logger.info(f"Chat session {session_id} started for {user_email}")

#         return APIResponse(
#             success=True,
#             message="Chat session started",
#             data=ChatResponse(
#                 session_id=session_id,
#                 finished=finished,
#                 reply=reply
#             )
#         )

#     except PromptInjectionError as e:
#         logger.warning(f"Prompt injection detected for {user_email}: {str(e)}")

#         return APIResponse(
#             success=False,
#             message="Unsafe input detected",
#             error=str(e)
#         )

#     except Exception as e:
#         logger.error(f"Error starting chat for {user_email}: {str(e)}")

#         return APIResponse(
#             success=False,
#             message="Failed to start chat session",
#             error=str(e)
#         )


# # =====================================================
# # CHAT (INTERVIEW CONTINUATION - JWT PROTECTED)
# # =====================================================
# @router.post("/chat", response_model=APIResponse[ChatResponse])
# def chat(req: ChatRequest, user_email: str = Depends(JWTBearer())):
#     """
#     Continue an existing chat session.
#     """
#     logger.debug(f"Continuing chat session {req.session_id} for user: {user_email}")

#     try:
#         result = chat_session(req.session_id, req.message)

#         if result["finished"]:
#             logger.info(f"Chat session {req.session_id} finished for {user_email}")

#             return APIResponse(
#                 success=True,
#                 message="Chat completed",
#                 data=ChatResponse(
#                     session_id=req.session_id,
#                     finished=True,
#                     final=result["final"]
#                 )
#             )

#         return APIResponse(
#             success=True,
#             message="Next question generated",
#             data=ChatResponse(
#                 session_id=req.session_id,
#                 finished=False,
#                 reply=result["reply"]
#             )
#         )

#     except PromptInjectionError as e:
#         logger.warning(f"Prompt injection detected in chat for {user_email}: {str(e)}")

#         return APIResponse(
#             success=False,
#             message="Unsafe input detected",
#             error=str(e)
#         )

#     except ValueError as e:
#         logger.warning(f"Invalid chat state for {user_email}: {str(e)}")

#         return APIResponse(
#             success=False,
#             message="Invalid chat state",
#             error=str(e)
#         )

#     except Exception as e:
#         logger.error(f"Error in chat for {user_email}: {str(e)}")

#         return APIResponse(
#             success=False,
#             message="Chat failed",
#             error=str(e)
#         )


# # =====================================================
# # RESET SESSION (JWT PROTECTED)
# # =====================================================
# @router.post("/reset", response_model=APIResponse[dict])
# def reset(req: ResetRequest, user_email: str = Depends(JWTBearer())):
#     """
#     Reset/clear a chat session from memory.
#     """
#     logger.info(f"Resetting chat session {req.session_id} for user: {user_email}")

#     try:
#         reset_session(req.session_id)

#         logger.info(f"Chat session {req.session_id} reset for {user_email}")

#         return APIResponse(
#             success=True,
#             message="Session reset successfully",
#             data={"session_id": req.session_id}
#         )

#     except Exception as e:
#         logger.error(f"Error resetting session {req.session_id}: {str(e)}")

#         return APIResponse(
#             success=False,
#             message="Failed to reset session",
#             error=str(e)
#         )


from fastapi import APIRouter, Depends
import logging

from api.schemas.chat import StartRequest, ChatRequest, ResetRequest
from api.schemas.response import APIResponse
from services.chat_service import start_session, chat_session, reset_session
from guardrails.guard_exceptions import PromptInjectionError
from auth.jwt_bearer import JWTBearer

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


# =====================================================
# START INTERVIEW
# =====================================================
@router.post("/start", response_model=None)
def start_chat(
    req: StartRequest,
    user_email: str = Depends(JWTBearer()),   # ✅ FIXED
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
    user_email: str = Depends(JWTBearer()),   # ✅ FIXED
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
    user_email: str = Depends(JWTBearer()),   # ✅ FIXED
):
    reset_session(req.session_id)

    return APIResponse(
        success=True,
        message="Session reset successfully",
        data={"session_id": req.session_id},
    )
