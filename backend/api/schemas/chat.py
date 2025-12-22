from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# =====================================================
# START INTERVIEW - ADD user_email
# =====================================================
class StartRequest(BaseModel):
    message: str
    user_email: str 


# =====================================================
# CHAT (INTERVIEW CONTINUATION)
# =====================================================
class ChatRequest(BaseModel):
    session_id: str
    message: str


# =====================================================
# RESET SESSION
# =====================================================
class ResetRequest(BaseModel):
    session_id: str


# =====================================================
# FINAL ASSESSMENT STRUCTURE
# =====================================================
class FinalAssessment(BaseModel):
    disease: str
    severity: str
    reason: str
    explanation: str


# =====================================================
# CHAT RESPONSE (QUESTION OR FINAL)
# =====================================================
class ChatResponse(BaseModel):
    session_id: str
    finished: bool
    reply: Optional[str] = None
    final: Optional[FinalAssessment] = None

    class Config:
        exclude_none = True


# =====================================================
# CHAT HISTORY SCHEMAS
# =====================================================
class MessageResponse(BaseModel):
    message_id: int
    role: str
    content: str
    message_order: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    session_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    message_count: int = 0
    
    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    session_id: str
    title: str
    status: str
    created_at: datetime
    messages: List[MessageResponse]
    assessment: Optional[FinalAssessment] = None
    
    class Config:
        from_attributes = True
