from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base
import uuid

class ChatSession(Base):
    __tablename__ = "sessions"
    __table_args__ = {'schema': 'chat'}
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email = Column(String(150), ForeignKey('auth.users.email', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(255))
    status = Column(String(20), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships (optional, for easier querying)
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    assessment = relationship("ChatAssessment", back_populates="session", uselist=False, cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name='check_role'),
        {'schema': 'chat'}
    )
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat.sessions.session_id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    session = relationship("ChatSession", back_populates="messages")

class ChatAssessment(Base):
    __tablename__ = "assessments"
    __table_args__ = {'schema': 'chat'}
    
    assessment_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat.sessions.session_id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    disease = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    session = relationship("ChatSession", back_populates="assessment")
