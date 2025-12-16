"""
Data models and schemas for the Medical Interview Chatbot API V2.
"""

from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    """Represents a single message in the conversation."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    session_id: str
    message: str

class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    session_id: str
    response: str
    finished: bool
    history: List[Message]

class ResetRequest(BaseModel):
    """Request model for resetting a session."""
    session_id: str

class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str
    message: str

class RootResponse(BaseModel):
    """Response model for root endpoint."""
    message: str
    docs: str
    endpoints: dict