from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

import logging

from database.chat_models import ChatSession, ChatMessage, ChatAssessment
from api.schemas.chat import SessionSummary, ConversationDetail, MessageResponse, FinalAssessment

logger = logging.getLogger(__name__)
from api.schemas.chat import SessionSummary, ConversationDetail, MessageResponse, FinalAssessment

def get_user_chat_history(db: Session, user_email: str, limit: int = 50) -> List[SessionSummary]:
    """
    Get all chat sessions for a user, ordered by most recent
    """
    logger.debug(f"Fetching chat history for user: {user_email}, limit: {limit}")
    sessions = db.query(
        ChatSession.session_id,
        ChatSession.title,
        ChatSession.status,
        ChatSession.created_at,
        ChatSession.updated_at,
        ChatSession.completed_at,
        func.count(ChatMessage.message_id).label('message_count')
    ).outerjoin(
        ChatMessage, ChatSession.session_id == ChatMessage.session_id
    ).filter(
        ChatSession.user_email == user_email
    ).group_by(
        ChatSession.session_id
    ).order_by(
        desc(ChatSession.created_at)
    ).limit(limit).all()
    
    result = [
        SessionSummary(
            session_id=str(s.session_id),
            title=s.title or "Untitled Chat",
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
            completed_at=s.completed_at,
            message_count=s.message_count or 0
        )
        for s in sessions
    ]
    logger.info(f"Retrieved {len(result)} chat sessions for {user_email}")
    return result

def get_conversation_by_id(db: Session, session_id: str, user_email: str) -> Optional[ConversationDetail]:
    """
    Get full conversation details including all messages and assessment
    """
    logger.debug(f"Fetching conversation {session_id} for user: {user_email}")
    # Validate session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.session_id == uuid.UUID(session_id),
        ChatSession.user_email == user_email
    ).first()
    
    if not session:
        logger.warning(f"Conversation {session_id} not found for user {user_email}")
        return None
    
    # Get all messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == uuid.UUID(session_id)
    ).order_by(ChatMessage.message_order).all()
    
    # Get assessment if exists
    assessment = db.query(ChatAssessment).filter(
        ChatAssessment.session_id == uuid.UUID(session_id)
    ).first()
    
    assessment_data = None
    if assessment:
        assessment_data = FinalAssessment(
            disease=assessment.disease,
            severity=assessment.severity,
            reason=assessment.reason,
            explanation=assessment.explanation
        )
    
    result = ConversationDetail(
        session_id=str(session.session_id),
        title=session.title or "Untitled Chat",
        status=session.status,
        created_at=session.created_at,
        messages=[
            MessageResponse(
                message_id=msg.message_id,
                role=msg.role,
                content=msg.content,
                message_order=msg.message_order,
                created_at=msg.created_at
            )
            for msg in messages
        ],
        assessment=assessment_data
    )
    logger.info(f"Retrieved conversation {session_id} with {len(messages)} messages for {user_email}")
    return result

def delete_conversation(db: Session, session_id: str, user_email: str) -> bool:
    """
    Delete a conversation (CASCADE will delete messages and assessment)
    """
    logger.info(f"Deleting conversation {session_id} for user: {user_email}")
    session = db.query(ChatSession).filter(
        ChatSession.session_id == uuid.UUID(session_id),
        ChatSession.user_email == user_email
    ).first()
    
    if not session:
        logger.warning(f"Conversation {session_id} not found for deletion by user {user_email}")
        return False
    
    db.delete(session)
    db.commit()
    logger.info(f"Conversation {session_id} deleted for {user_email}")
    return True

def get_grouped_history(db: Session, user_email: str):
    """
    Get chat history grouped by time periods (Today, Yesterday, This Week, etc.)
    """
    logger.debug(f"Fetching grouped history for user: {user_email}")
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    all_sessions = get_user_chat_history(db, user_email)
    
    grouped = {
        "today": [],
        "yesterday": [],
        "this_week": [],
        "this_month": [],
        "older": []
    }
    
    for session in all_sessions:
        created = session.created_at.replace(tzinfo=None)  # Remove timezone for comparison
        
        if created >= today_start:
            grouped["today"].append(session)
        elif created >= yesterday_start:
            grouped["yesterday"].append(session)
        elif created >= week_start:
            grouped["this_week"].append(session)
        elif created >= month_start:
            grouped["this_month"].append(session)
        else:
            grouped["older"].append(session)
    
    logger.info(f"Grouped history for {user_email}: { {k: len(v) for k, v in grouped.items()} }")
    return grouped
