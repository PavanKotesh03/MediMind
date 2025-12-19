from pydantic import BaseModel
from typing import Optional


# =====================================================
# START INTERVIEW
# =====================================================
class StartRequest(BaseModel):
    message: str


# =====================================================
# CHAT (INTERVIEW CONTINUATION)
# =====================================================
class ChatRequest(BaseModel):
    session_id: str
    message: str


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
        exclude_none = True  # 🔑 IMPORTANT: removes reply=null
