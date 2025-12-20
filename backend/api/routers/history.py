from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from api.schemas.chat import SessionSummary, ConversationDetail
from services.history_service import (
    get_user_chat_history,
    get_conversation_by_id,
    delete_conversation,
    get_grouped_history
)
from database.connection import get_db

router = APIRouter(prefix="/chat/history", tags=["Chat History"])

# =====================================================
# GET USER'S CHAT HISTORY
# =====================================================
@router.get("/", response_model=List[SessionSummary])
def get_history(
    user_email: str = Query(..., description="User's email"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all chat sessions for a user
    
    - **user_email**: Email of the logged-in user
    - **limit**: Maximum number of sessions to return (default 50)
    """
    return get_user_chat_history(db, user_email, limit)

# =====================================================
# GET GROUPED HISTORY (Today, Yesterday, etc.)
# =====================================================
@router.get("/grouped")
def get_history_grouped(
    user_email: str = Query(..., description="User's email"),
    db: Session = Depends(get_db)
):
    """
    Get chat history grouped by time periods
    """
    return get_grouped_history(db, user_email)

# =====================================================
# GET SPECIFIC CONVERSATION
# =====================================================
@router.get("/{session_id}", response_model=ConversationDetail)
def get_conversation(
    session_id: str,
    user_email: str = Query(..., description="User's email"),
    db: Session = Depends(get_db)
):
    """
    Get full conversation details including all messages
    
    - **session_id**: UUID of the conversation
    - **user_email**: Email of the logged-in user (for security)
    """
    conversation = get_conversation_by_id(db, session_id, user_email)
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found or you don't have access"
        )
    
    return conversation

# =====================================================
# DELETE CONVERSATION
# =====================================================
@router.delete("/{session_id}")
def delete_chat(
    session_id: str,
    user_email: str = Query(..., description="User's email"),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation permanently
    
    - **session_id**: UUID of the conversation
    - **user_email**: Email of the logged-in user (for security)
    """
    success = delete_conversation(db, session_id, user_email)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found or you don't have access"
        )
    
    return {
        "status": "success",
        "message": "Conversation deleted",
        "session_id": session_id
    }
