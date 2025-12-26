from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from auth.jwt_handler import verify_token

from api.schemas.chat import SessionSummary, ConversationDetail
from services.history_service import (
    get_user_chat_history,
    get_conversation_by_id,
    delete_conversation,
    get_grouped_history
)
from database.connection import get_db

router = APIRouter(tags=["Chat History"])

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user email from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        return verify_token(credentials.credentials)
    except HTTPException as e:
        # Re-raise with proper WWW-Authenticate header
        raise HTTPException(
            status_code=401,
            detail=str(e.detail),
            headers={"WWW-Authenticate": "Bearer"}
        )

# =====================================================
# GET USER'S CHAT HISTORY
# =====================================================
@router.get("/", response_model=List[SessionSummary])
def get_history(
    user_email: str = Query(..., description="User's email"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all chat sessions for a user"""
    if current_user != user_email:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Token user '{current_user}' cannot access '{user_email}' data"
        )
    
    try:
        return get_user_chat_history(db, user_email, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

# =====================================================
# GET GROUPED HISTORY
# =====================================================
@router.get("/grouped")
def get_history_grouped(
    user_email: str = Query(..., description="User's email"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get chat history grouped by time periods"""
    if current_user != user_email:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Token user '{current_user}' cannot access '{user_email}' data"
        )
    
    try:
        return get_grouped_history(db, user_email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch grouped history: {str(e)}")

# =====================================================
# GET SPECIFIC CONVERSATION
# =====================================================
@router.get("/{session_id}", response_model=ConversationDetail)
def get_conversation(
    session_id: str,
    user_email: str = Query(..., description="User's email"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get full conversation details including all messages"""
    if current_user != user_email:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Token user '{current_user}' cannot access '{user_email}' data"
        )
    
    try:
        conversation = get_conversation_by_id(db, session_id, user_email)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation '{session_id}' not found or you don't have access"
            )
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")

# =====================================================
# DELETE CONVERSATION
# =====================================================
@router.delete("/{session_id}")
def delete_chat(
    session_id: str,
    user_email: str = Query(..., description="User's email"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Delete a conversation permanently"""
    if current_user != user_email:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Token user '{current_user}' cannot access '{user_email}' data"
        )
    
    try:
        success = delete_conversation(db, session_id, user_email)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation '{session_id}' not found or you don't have access"
            )
        
        return {
            "status": "success",
            "message": "Conversation deleted",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")
