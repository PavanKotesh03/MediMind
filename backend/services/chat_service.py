import uuid
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import AsyncGenerator
import logging

from llm.interview_agent import MedicalInterviewAgent
from llm.explanation_agent import MedicalExplanationAgent
from llm.fact_extractor import extract_facts
from rules.disease_engine import DiseasePatternEngine
from scripts.step4_query_system_hybrid import hybrid_search

from guardrails.input_guard import sanitize_user_input
from guardrails.scope_guard import ensure_medical_scope

from database.connection import SessionLocal
from database.chat_models import ChatSession, ChatMessage, ChatAssessment

logger = logging.getLogger(__name__)


def retriever(query, top_k=5):
    results = hybrid_search(query)
    return [
        {
            "text": r["text"],
            "metadata": r.get("metadata", {})
        }
        for r in results[:top_k]
    ]


disease_engine = DiseasePatternEngine()
explanation_agent = MedicalExplanationAgent(retriever)

# In-memory sessions
_sessions = {}


def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False


def _generate_title(first_message: str) -> str:
    """Generate conversation title from first user message"""
    title = first_message.strip()[:50]
    if len(first_message) > 50:
        title += "..."
    return title


# =====================================================
#  RESTORE SESSION FROM DATABASE
# =====================================================
def restore_session_from_db(session_id: str, db: DBSession) -> bool:
    """
    Restore an active session from database to memory.
    Returns True if successful, False if session not found or completed.
    """
    if session_id in _sessions:
        return True
    
    try:
        db_session = db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id),
            ChatSession.status == 'active'
        ).first()
        
        if not db_session:
            return False
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == uuid.UUID(session_id)
        ).order_by(ChatMessage.message_order).all()
        
        conversation_history = []
        for msg in messages:
            if msg.role in ['user', 'assistant']:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        interview = MedicalInterviewAgent()
        interview.history = conversation_history
        interview.finished = False
        
        _sessions[session_id] = {
            "interview": interview,
            "final": None,
            "message_count": len(messages),
            "user_email": db_session.user_email
        }
        
        logger.info(f"Restored session {session_id} with {len(messages)} messages")
        return True
        
    except Exception as e:
        logger.error(f"Error restoring session: {e}")
        return False


# =====================================================
# START SESSION (NON-STREAMING)
# =====================================================
def start_session(user_message: str | None, user_email: str):
    """
    Start new chat session and save to database (non-streaming version)
    """
    logger.info(f"Starting new chat session for user: {user_email}")
    
    session_id = uuid.uuid4()
    interview = MedicalInterviewAgent()
    
    if user_message:
        clean_input = sanitize_user_input(user_message)
        ensure_medical_scope(clean_input)
        reply = interview.start(clean_input)
        title = _generate_title(user_message)
        message_count = 3
    else:
        reply = "Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns."
        title = "New Chat"
        message_count = 1
        interview.history.append({"role": "assistant", "content": reply})
    
    _sessions[str(session_id)] = {
        "interview": interview,
        "final": None,
        "message_count": message_count,
        "user_email": user_email
    }
    
    db = SessionLocal()
    try:
        db_session = ChatSession(
            session_id=session_id,
            user_email=user_email,
            title=title,
            status='active'
        )
        db.add(db_session)
        db.flush()
        
        greeting = ChatMessage(
            session_id=session_id,
            role='assistant',
            content='Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.',
            message_order=1
        )
        db.add(greeting)
        
        if user_message:
            user_msg = ChatMessage(
                session_id=session_id,
                role='user',
                content=user_message,
                message_order=2
            )
            db.add(user_msg)
            
            bot_reply = ChatMessage(
                session_id=session_id,
                role='assistant',
                content=reply,
                message_order=3
            )
            db.add(bot_reply)
        
        db.commit()
        logger.info(f"Chat session {session_id} started and saved for {user_email}")
        
    except (IntegrityError, SQLAlchemyError) as e:
        db.rollback()
        logger.error(f"Database error starting session: {e}")
        raise ValueError(f"Failed to save session: {e}")
    finally:
        db.close()
    
    return str(session_id), reply, interview.finished


# =====================================================
# START SESSION STREAMING (NEW)
# =====================================================
async def start_session_streaming(user_message: str | None, user_email: str) -> AsyncGenerator[dict, None]:
    """
    Start new chat session with streaming response
    Yields: {"type": "session_id", "data": ...} or {"type": "token", "data": ...}
    """
    logger.info(f"Starting new streaming chat session for user: {user_email}")
    
    session_id = uuid.uuid4()
    interview = MedicalInterviewAgent()
    
    # First yield the session ID
    yield {
        "type": "session_id",
        "data": str(session_id)
    }
    
    if user_message:
        clean_input = sanitize_user_input(user_message)
        ensure_medical_scope(clean_input)
        title = _generate_title(user_message)
        
        # Stream the response
        full_response = []
        async for token in interview.start_streaming(clean_input):
            full_response.append(token)
            yield {
                "type": "token",
                "data": token
            }
        
        reply = "".join(full_response)
        message_count = 3
    else:
        reply = "Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns."
        title = "New Chat"
        message_count = 1
        interview.history.append({"role": "assistant", "content": reply})
        
        # Yield the greeting
        yield {
            "type": "token",
            "data": reply
        }
    
    # Store in memory
    _sessions[str(session_id)] = {
        "interview": interview,
        "final": None,
        "message_count": message_count,
        "user_email": user_email
    }
    
    # Save to database
    db = SessionLocal()
    try:
        db_session = ChatSession(
            session_id=session_id,
            user_email=user_email,
            title=title,
            status='active'
        )
        db.add(db_session)
        db.flush()
        
        greeting = ChatMessage(
            session_id=session_id,
            role='assistant',
            content='Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.',
            message_order=1
        )
        db.add(greeting)
        
        if user_message:
            user_msg = ChatMessage(
                session_id=session_id,
                role='user',
                content=user_message,
                message_order=2
            )
            db.add(user_msg)
            
            bot_reply = ChatMessage(
                session_id=session_id,
                role='assistant',
                content=reply,
                message_order=3
            )
            db.add(bot_reply)
        
        db.commit()
        logger.info(f"Streaming session {session_id} saved to database")
        
    except (IntegrityError, SQLAlchemyError) as e:
        db.rollback()
        logger.error(f"Database error in streaming session: {e}")
    finally:
        db.close()
    
    # Signal completion
    yield {
        "type": "done",
        "data": {
            "finished": interview.finished
        }
    }


# =====================================================
# CHAT SESSION STREAMING (WITH END_OF_INTERVIEW FILTERING)
# =====================================================
async def chat_session_streaming(session_id: str, user_message: str) -> AsyncGenerator[dict, None]:
    """
    Continue chat session with streaming response
    Yields: {"type": "token"|"finalizing"|"explanation_token"|"final"|"done", "data": ...}
    """
    logger.info(f"Streaming chat for session {session_id}")
    
    if not _is_valid_uuid(session_id):
        logger.warning(f"Invalid session_id: {session_id}")
        raise ValueError("Invalid session_id")
    
    # Restore session if needed
    if session_id not in _sessions:
        logger.info(f"Restoring session {session_id} from database")
        db = SessionLocal()
        try:
            if not restore_session_from_db(session_id, db):
                raise ValueError("Session not found or has been completed. Please start a new chat.")
        finally:
            db.close()
    
    # Guardrails
    clean_input = sanitize_user_input(user_message)
    ensure_medical_scope(clean_input)
    
    session = _sessions[session_id]
    interview = session["interview"]
    message_count = session["message_count"]
    
    # 🆕 Stream the reply with BULLETPROOF END_OF_INTERVIEW filtering
    full_response = []
    finalizing_sent = False
    buffer = ""  # Buffer to handle multi-token patterns

    async for token in interview.reply_streaming(clean_input):
        full_response.append(token)
        buffer += token
        
        # Check if buffer contains END_OF_INTERVIEW (case insensitive)
        if "end_of_interview" in buffer.lower() or "<end_of_interview>" in buffer.lower():
            # Send finalizing message only once
            if not finalizing_sent:
                yield {
                    "type": "finalizing",
                    "data": "Finalizing your assessment..."
                }
                finalizing_sent = True
            
            # Clear buffer and stop sending tokens
            buffer = ""
            continue
        
        # If we've already sent finalizing, don't send more tokens
        if finalizing_sent:
            continue
        
        # Yield normal tokens
        yield {
            "type": "token",
            "data": token
        }
        
        # Keep buffer size manageable (last 30 chars to detect pattern)
        if len(buffer) > 30:
            buffer = buffer[-30:]

    reply = "".join(full_response)

    
    # Save messages to database
    db = SessionLocal()
    try:
        user_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='user',
            content=user_message,
            message_order=message_count + 1
        )
        db.add(user_msg)
        
        bot_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='assistant',
            content=reply,
            message_order=message_count + 2
        )
        db.add(bot_msg)
        
        update_data = {"updated_at": datetime.utcnow()}
        
        if message_count <= 1:
            update_data["title"] = _generate_title(user_message)
        
        db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id)
        ).update(update_data)
        
        db.commit()
        session["message_count"] = message_count + 2
        
    except (IntegrityError, SQLAlchemyError) as e:
        db.rollback()
        logger.error(f"Failed to save streaming messages: {e}")
    finally:
        db.close()
    
    # CHECK IF INTERVIEW FINISHED AND STREAM EXPLANATION
    if interview.finished:
        logger.info(f"Interview finished for session {session_id}")
        
        if session["final"] is None:
            facts = extract_facts(interview.history)
            matches = disease_engine.evaluate(facts)
            
            if matches:
                top = matches[0]
                logger.info(f"Disease match found: {top['disease']}")
            else:
                logger.warning("No disease match, using fallback")
                top = {
                    "disease": "Undifferentiated Symptom Pattern",
                    "severity": "MEDIUM",
                    "reason": "Symptoms require further medical evaluation"
                }
            
            # STREAM THE EXPLANATION
            logger.info(f"Streaming explanation for {top['disease']}")
            explanation_parts = []
            
            try:
                async for token in explanation_agent.explain_streaming(
                    disease=top["disease"],
                    history=interview.history
                ):
                    explanation_parts.append(token)
                    
                    # Yield each explanation token as it arrives
                    yield {
                        "type": "explanation_token",
                        "data": token
                    }
            except Exception as e:
                logger.error(f"Error streaming explanation: {e}")
                # Fallback explanation if streaming fails
                fallback = f"Assessment complete for {top['disease']}. The symptoms you described are consistent with this condition. Please consult a healthcare provider for proper evaluation."
                explanation_parts = [fallback]
                yield {
                    "type": "explanation_token",
                    "data": fallback
                }
            
            final_explanation = ''.join(explanation_parts).strip()
            
            session["final"] = {
                "disease": top["disease"],
                "severity": top["severity"],
                "reason": top["reason"],
                "explanation": final_explanation
            }
            
            # Save assessment to database
            db = SessionLocal()
            try:
                assessment = ChatAssessment(
                    session_id=uuid.UUID(session_id),
                    disease=top["disease"],
                    severity=top["severity"],
                    reason=top["reason"],
                    explanation=final_explanation
                )
                db.add(assessment)
                
                db.query(ChatSession).filter(
                    ChatSession.session_id == uuid.UUID(session_id)
                ).update({
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                })
                
                db.commit()
                logger.info(f"Assessment saved for session {session_id}")
                
            except (IntegrityError, SQLAlchemyError) as e:
                db.rollback()
                logger.error(f"Failed to save assessment: {e}")
            finally:
                db.close()
        
        # Yield final assessment metadata
        yield {
            "type": "final",
            "data": session["final"]
        }
    
    # Signal completion
    yield {
        "type": "done",
        "data": {
            "finished": interview.finished
        }
    }



# =====================================================
# CHAT SESSION (NON-STREAMING - KEEP FOR BACKWARDS COMPATIBILITY)
# =====================================================
def chat_session(session_id: str, user_message: str):
    """Non-streaming version - kept for backwards compatibility"""
    logger.debug(f"Continuing chat session {session_id}")
    
    if not _is_valid_uuid(session_id):
        logger.warning(f"Invalid session_id: {session_id}")
        raise ValueError("Invalid session_id")
    
    if session_id not in _sessions:
        logger.info(f"Restoring session {session_id} from database")
        db = SessionLocal()
        try:
            if not restore_session_from_db(session_id, db):
                raise ValueError("Session not found or has been completed. Please start a new chat.")
        finally:
            db.close()
    
    clean_input = sanitize_user_input(user_message)
    ensure_medical_scope(clean_input)
    
    session = _sessions[session_id]
    interview = session["interview"]
    message_count = session["message_count"]
    
    reply = interview.reply(clean_input)
    
    # Save to database
    db = SessionLocal()
    try:
        user_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='user',
            content=user_message,
            message_order=message_count + 1
        )
        db.add(user_msg)
        
        bot_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='assistant',
            content=reply,
            message_order=message_count + 2
        )
        db.add(bot_msg)
        
        update_data = {"updated_at": datetime.utcnow()}
        
        if message_count <= 1:
            update_data["title"] = _generate_title(user_message)
        
        db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id)
        ).update(update_data)
        
        db.commit()
        session["message_count"] = message_count + 2
        
    except (IntegrityError, SQLAlchemyError) as e:
        db.rollback()
        logger.error(f"Failed to save messages: {e}")
    finally:
        db.close()
    
    if interview.finished:
        logger.info(f"Interview finished for session {session_id}")
        
        if session["final"] is None:
            facts = extract_facts(interview.history)
            matches = disease_engine.evaluate(facts)
            
            if matches:
                top = matches[0]
            else:
                top = {
                    "disease": "Undifferentiated Symptom Pattern",
                    "severity": "MEDIUM",
                    "reason": "Symptoms require further medical evaluation"
                }
            
            # Use non-streaming explain for backwards compatibility
            explanation = explanation_agent.explain(
                disease=top["disease"],
                history=interview.history
            )
            
            session["final"] = {
                "disease": top["disease"],
                "severity": top["severity"],
                "reason": top["reason"],
                "explanation": explanation
            }
            
            db = SessionLocal()
            try:
                assessment = ChatAssessment(
                    session_id=uuid.UUID(session_id),
                    disease=top["disease"],
                    severity=top["severity"],
                    reason=top["reason"],
                    explanation=explanation
                )
                db.add(assessment)
                
                db.query(ChatSession).filter(
                    ChatSession.session_id == uuid.UUID(session_id)
                ).update({
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                })
                
                db.commit()
                
            except (IntegrityError, SQLAlchemyError) as e:
                db.rollback()
                logger.error(f"Failed to save assessment: {e}")
            finally:
                db.close()
        
        return {
            "finished": True,
            "final": session["final"]
        }
    
    return {
        "finished": False,
        "reply": reply
    }


# =====================================================
# RESET SESSION
# =====================================================
def reset_session(session_id: str):
    """Remove session from memory (DB record stays for history)"""
    logger.info(f"Resetting session {session_id}")
    _sessions.pop(session_id, None)
