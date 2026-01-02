import uuid
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Generator, Dict, Any
import logging
import time

from llm.interview_agent import MedicalInterviewAgent
from llm.explanation_agent import MedicalExplanationAgent
from llm.fact_extractor import extract_facts
from rules.disease_engine import DiseasePatternEngine
from scripts.step4_query_system_hybrid import hybrid_search

from guardrails.input_guard import sanitize_user_input
from guardrails.scope_guard import ensure_medical_scope
from guardrails.guard_exceptions import PromptInjectionError

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
explanation_agent = MedicalExplanationAgent(retriever)  # FIXED - Pass retriever

# In-memory sessions (still needed for active chat)
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
# RESTORE SESSION FROM DATABASE
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
            logger.warning(f"Session {session_id} not found or not active")
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
        
        interview = MedicalInterviewAgent(retriever)
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
        logger.error(f"Error restoring session {session_id}: {e}")
        return False


# =====================================================
# START SESSION (creates empty session)
# =====================================================
def start_session(user_message: str, user_email: str):
    """
    Start new empty chat session and save to database
    Called by: Login and "New Chat" button
    """
    logger.info(f"Starting new empty session for user: {user_email}")
    
    # Create interview agent
    interview = MedicalInterviewAgent(retriever)
    
    # Generate session ID
    session_id = uuid.uuid4()
    
    # Store in memory for active chat
    _sessions[str(session_id)] = {
        "interview": interview,
        "final": None,
        "message_count": 1,  # Only greeting message
        "user_email": user_email
    }
    
    # Save to database
    db = SessionLocal()
    try:
        # Create session record
        db_session = ChatSession(
            session_id=session_id,
            user_email=user_email,
            title="New Chat",  # Will be updated with first message
            status='active'
        )
        db.add(db_session)
        db.flush()
        
        # Save greeting message only
        greeting = ChatMessage(
            session_id=session_id,
            role='assistant',
            content='Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.',
            message_order=1
        )
        db.add(greeting)
        
        db.commit()
        db.flush()  # Ensure data is written
        logger.info(f"Empty session {session_id} created for {user_email}")
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error starting session: {e}")
        raise ValueError(f"Failed to save session: {e}")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error starting session: {e}")
        raise ValueError(f"Database error: {e}")
        
    finally:
        db.close()
    
    greeting_msg = 'Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.'
    return str(session_id), greeting_msg, False


# =====================================================
# STREAMING CHAT SESSION (handles all messages + DB save)
# =====================================================
def chat_session_streaming(session_id: str, user_message: str) -> Generator[Dict[str, Any], None, None]:
    """
    Stream chat responses and save to database
    Handles FIRST message and ALL subsequent messages
    """
    logger.info(f"Streaming chat for session {session_id}")
    
    if not _is_valid_uuid(session_id):
        logger.warning(f"Invalid session_id: {session_id}")
        yield {"type": "error", "error": "Invalid session ID"}
        return
    
    # Restore session from DB if not in memory
    if session_id not in _sessions:
        logger.info(f"Restoring session {session_id} from database")
        db = SessionLocal()
        try:
            if not restore_session_from_db(session_id, db):
                logger.warning(f"Session {session_id} not found or completed")
                yield {"type": "error", "error": "Session not found or has been completed"}
                return
        finally:
            db.close()
    
    # Guardrails
    try:
        clean_input = sanitize_user_input(user_message)
        ensure_medical_scope(clean_input)
    except PromptInjectionError as e:
        logger.warning(f"Prompt injection detected: {e}")
        yield {"type": "error", "error": str(e)}
        return
    
    session = _sessions[session_id]
    interview = session["interview"]
    message_count = session["message_count"]
    
    # Save user message to database FIRST
    db = SessionLocal()
    try:
        user_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='user',
            content=user_message,
            message_order=message_count + 1
        )
        db.add(user_msg)
        
        # Update session title if this is first user message
        db_session = db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id)
        ).first()
        
        if db_session and db_session.title == "New Chat":
            db_session.title = _generate_title(user_message)
        
        db_session.updated_at = datetime.utcnow()
        
        db.commit()
        db.flush()  # Ensure user message is written
        logger.info(f"User message saved to DB for session {session_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save user message: {e}")
        yield {"type": "error", "error": "Failed to save message"}
        return
    finally:
        db.close()
    
    # Get reply from interview agent
    try:
        if message_count == 1:
            # First message - use start()
            logger.info(f"Starting interview for session {session_id}")
            reply = interview.start(clean_input)
        else:
            # Subsequent messages - use reply()
            logger.info(f"Continuing interview for session {session_id}")
            reply = interview.reply(clean_input)
    except Exception as e:
        logger.error(f"Interview agent error: {e}")
        yield {"type": "error", "error": "Interview processing failed"}
        return
    
    # Stream response word by word
    words = reply.split()
    for word in words:
        yield {
            "type": "text",
            "content": word + " "
        }
        time.sleep(0.02)  # Small delay for smooth streaming
    
    # Save assistant reply to database
    db = SessionLocal()
    try:
        bot_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='assistant',
            content=reply,
            message_order=message_count + 2
        )
        db.add(bot_msg)
        db.commit()
        db.flush()  # Ensure assistant message is written
        
        session["message_count"] = message_count + 2
        logger.info(f"Assistant reply saved to DB for session {session_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save assistant reply: {e}")
    finally:
        db.close()
    
    # Check if interview finished
    if interview.finished:
        logger.info(f"Interview finished for session {session_id}")
        
        if session["final"] is None:
            # Generate assessment
            try:
                facts = extract_facts(interview.history)
                matches = disease_engine.evaluate(facts)
                
                if matches:
                    top = matches[0]
                    logger.info(f"Disease match: {top['disease']}")
                else:
                    logger.warning(f"No disease match, using fallback")
                    top = {
                        "disease": "Undifferentiated Symptom Pattern",
                        "severity": "MEDIUM",
                        "reason": "Symptoms require further medical evaluation"
                    }
                
                # Try to generate explanation
                logger.info(f"Generating explanation for: {top['disease']}")
                explanation = None
                
                try:
                    # Call explanation agent
                    explanation = explanation_agent.explain(
                        disease=top["disease"],
                        history=interview.history
                    )
                    logger.info("Explanation generated successfully")
                except Exception as exp_error:
                    logger.warning(f"Explanation generation failed: {exp_error}")
                    explanation = None
                
                # If explanation failed, use detailed fallback
                if not explanation:
                    logger.info("Using detailed fallback explanation")
                    
                    # Extract key symptoms from history
                    symptoms_list = []
                    duration = "several days"
                    
                    for msg in interview.history:
                        if msg["role"] == "user":
                            content = msg["content"].lower()
                            # Extract duration
                            if any(d in content for d in ["day", "days", "week", "weeks", "month"]):
                                duration = msg["content"]
                            # Extract symptoms
                            if any(s in content for s in ["fever", "pain", "cough", "headache", "throat", "breathing"]):
                                if msg["content"] not in symptoms_list and len(msg["content"]) < 50:
                                    symptoms_list.append(msg["content"])
                    
                    symptoms_text = ", ".join(symptoms_list[:5]) if symptoms_list else "your reported symptoms"
                    
                    explanation = f"""Let's break down your symptoms step by step:

Primary Symptoms: You reported {symptoms_text}.

Duration: Your symptoms have been present for {duration}.

Disease Assessment: Based on the pattern of symptoms, this appears to be {top['disease']}.

Why this diagnosis?
The combination of symptoms you described are characteristic of {top['disease']}. This is a common condition that typically resolves on its own with proper rest and care.

Severity Level - {top['severity']}:
{top['reason']}. Your symptoms don't show severe warning signs that would require immediate emergency care.

What you should know:
- This condition is usually self-limiting, meaning it gets better on its own
- Rest and staying hydrated are important
- Monitor your symptoms for any worsening

When to seek immediate medical attention:
- If fever persists beyond 3-4 days or gets very high (above 103F/39.4C)
- If you develop severe difficulty breathing
- If you experience severe weakness, dizziness, or confusion
- If symptoms significantly worsen instead of improving

General Recommendations:
- Get adequate rest
- Stay well hydrated (water, clear soups, herbal teas)
- Use over-the-counter fever reducers if needed (as per package instructions)
- Monitor your symptoms daily

Important Note: This assessment is based on the information you provided during our conversation. It is meant for informational purposes only and should not replace a proper medical evaluation. Please consult with a healthcare provider for a definitive diagnosis and personalized treatment plan, especially if symptoms persist or worsen."""
                
                session["final"] = {
                    "disease": top["disease"],
                    "severity": top["severity"],
                    "reason": top["reason"],
                    "explanation": explanation
                }
                
                logger.info(f"Assessment completed successfully")
                
            except Exception as e:
                logger.error(f"Error generating assessment: {e}", exc_info=True)
                session["final"] = {
                    "disease": "Assessment Error",
                    "severity": "UNKNOWN",
                    "reason": "Unable to complete assessment",
                    "explanation": "An error occurred while processing your symptoms. Please try again or consult a healthcare provider."
                }
            
            # Save assessment to database
            db = SessionLocal()
            try:
                assessment = ChatAssessment(
                    session_id=uuid.UUID(session_id),
                    disease=session["final"]["disease"],
                    severity=session["final"]["severity"],
                    reason=session["final"]["reason"],
                    explanation=session["final"]["explanation"]
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
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to save assessment: {e}", exc_info=True)
            finally:
                db.close()
        
        # Stream the final assessment word by word
        final_data = session["final"]
        
        # Stream header
        yield {"type": "final_header", "data": {
            "disease": final_data["disease"],
            "severity": final_data["severity"],
            "reason": final_data["reason"]
        }}
        
        time.sleep(0.1)
        
        # Stream explanation word by word
        explanation_words = final_data["explanation"].split()
        for word in explanation_words:
            yield {
                "type": "final_text",
                "content": word + " "
            }
            time.sleep(0.03)
        
        # Mark as finished
        yield {
            "type": "final_complete",
            "finished": True
        }
        
        logger.info(f"Stream completed successfully for session {session_id}")


# =====================================================
# OLD CHAT SESSION (kept for backward compatibility)
# =====================================================
def chat_session(session_id: str, user_message: str):
    """Legacy function - use chat_session_streaming instead"""
    logger.debug(f"Continuing chat session {session_id} (legacy mode)")
    if not _is_valid_uuid(session_id):
        logger.warning(f"Invalid session_id: {session_id}")
        raise ValueError("Invalid session_id")

    if session_id not in _sessions:
        logger.info(f"Restoring session {session_id} from database")
        db = SessionLocal()
        try:
            if not restore_session_from_db(session_id, db):
                logger.warning(f"Session {session_id} not found or completed")
                raise ValueError("Session not found or has been completed. Please start a new chat.")
        finally:
            db.close()

    clean_input = sanitize_user_input(user_message)
    ensure_medical_scope(clean_input)

    session = _sessions[session_id]
    interview = session["interview"]
    message_count = session["message_count"]
    
    reply = interview.reply(clean_input)
    
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
        
        db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id)
        ).update({"updated_at": datetime.utcnow()})
        
        db.commit()
        db.flush()
        session["message_count"] = message_count + 2
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to save messages for session {session_id}: {e}")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error saving messages for session {session_id}: {e}")
        
    finally:
        db.close()

    if interview.finished:
        logger.info(f"Interview finished for session {session_id}")
        if session["final"] is None:
            facts = extract_facts(interview.history)
            matches = disease_engine.evaluate(facts)

            if matches:
                top = matches[0]
                logger.info(f"Disease match for session {session_id}: {top['disease']}")
            else:
                logger.warning(f"No disease match for session {session_id}, using fallback")
                top = {
                    "disease": "Undifferentiated Symptom Pattern",
                    "severity": "MEDIUM",
                    "reason": "Symptoms require further medical evaluation"
                }

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
                db.flush()
                logger.info(f"Assessment saved for completed session {session_id}")
                
            except IntegrityError as e:
                db.rollback()
                logger.error(f"Failed to save assessment for session {session_id}: {e}")
                
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Database error saving assessment for session {session_id}: {e}")
                
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
    logger.info(f"Session {session_id} removed from memory")
