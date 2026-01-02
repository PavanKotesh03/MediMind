from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from auth.jwt_bearer import JWTBearer
from api.schemas.chat import ConversationDetail
from api.schemas.response import APIResponse
from api.schemas.history import GroupedHistory
from services.history_service import (
    get_conversation_by_id,
    delete_conversation,
    get_grouped_history
)
from database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat History"])


# =====================================================
# GET GROUPED HISTORY (JWT ONLY)
# =====================================================
@router.get("/grouped", response_model=APIResponse[GroupedHistory])
def get_history_grouped(
    db: Session = Depends(get_db),
    current_user: str = Depends(JWTBearer()),
):
    logger.info(f"Fetching grouped history for user: {current_user}")

    history = get_grouped_history(db, current_user)

    return APIResponse(
        success=True,
        message="History fetched successfully",
        data=history
    )


# =====================================================
# GET SPECIFIC CONVERSATION (JWT ONLY)
# =====================================================
@router.get("/{session_id}", response_model=APIResponse[ConversationDetail])
def get_conversation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(JWTBearer()),
):
    logger.info(f"Fetching conversation {session_id} for user: {current_user}")

    conversation = get_conversation_by_id(db, session_id, current_user)

    if not conversation:
        return APIResponse(
            success=False,
            message="Conversation not found",
            error="Conversation does not exist or access denied"
        )

    return APIResponse(
        success=True,
        message="Conversation fetched successfully",
        data=conversation
    )


# =====================================================
# DELETE CONVERSATION (JWT ONLY)
# =====================================================
@router.delete("/{session_id}", response_model=APIResponse[dict])
def delete_chat(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(JWTBearer()),
):
    logger.info(f"Deleting conversation {session_id} for user: {current_user}")

    success = delete_conversation(db, session_id, current_user)

    if not success:
        return APIResponse(
            success=False,
            message="Conversation not found",
            error="Conversation does not exist or access denied"
        )

    return APIResponse(
        success=True,
        message="Conversation deleted successfully",
        data={"session_id": session_id}
    )
