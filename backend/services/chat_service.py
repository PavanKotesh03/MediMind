import uuid
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from llm.interview_agent import MedicalInterviewAgent
from llm.explanation_agent import MedicalExplanationAgent
from llm.fact_extractor import extract_facts
from rules.disease_engine import DiseasePatternEngine
from scripts.step4_query_system_hybrid import hybrid_search

from guardrails.input_guard import sanitize_user_input
from guardrails.scope_guard import ensure_medical_scope

from database.connection import SessionLocal
from database.chat_models import ChatSession, ChatMessage, ChatAssessment


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
# ✅ NEW: RESTORE SESSION FROM DATABASE
# =====================================================
def restore_session_from_db(session_id: str, db: DBSession) -> bool:
    """
    Restore an active session from database to memory.
    Returns True if successful, False if session not found or completed.
    """
    # Already in memory
    if session_id in _sessions:
        return True
    
    try:
        # Get session from database
        db_session = db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id),
            ChatSession.status == 'active'
        ).first()
        
        if not db_session:
            return False
        
        # Get all messages for this session
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == uuid.UUID(session_id)
        ).order_by(ChatMessage.message_order).all()
        
        # Rebuild conversation history for interview agent
        conversation_history = []
        for msg in messages:
            if msg.role in ['user', 'assistant']:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Recreate interview agent with history
        interview = MedicalInterviewAgent(retriever)
        interview.history = conversation_history
        interview.finished = False  # Will continue interview
        
        # Restore session state
        _sessions[session_id] = {
            "interview": interview,
            "final": None,
            "message_count": len(messages),
            "user_email": db_session.user_email
        }
        
        print(f"✅ Restored session {session_id} with {len(messages)} messages")
        return True
        
    except Exception as e:
        print(f"❌ Error restoring session: {e}")
        return False


# =====================================================
# START SESSION (with DB save)
# =====================================================
def start_session(user_message: str, user_email: str):
    """
    Start new chat session and save to database
    """
    # 🔒 GUARDRAILS
    clean_input = sanitize_user_input(user_message)
    ensure_medical_scope(clean_input)

    # Create interview
    interview = MedicalInterviewAgent(retriever)
    reply = interview.start(clean_input)
    
    session_id = uuid.uuid4()
    
    # Store in memory for active chat
    _sessions[str(session_id)] = {
        "interview": interview,
        "final": None,
        "message_count": 3,
        "user_email": user_email
    }
    
    # 💾 Save to database with proper transaction handling
    db = SessionLocal()
    try:
        # 1. Create session record FIRST
        db_session = ChatSession(
            session_id=session_id,
            user_email=user_email,
            title=_generate_title(user_message),
            status='active'
        )
        db.add(db_session)
        db.flush()  # ✅ FIX: Flush to commit session_id before messages
        
        # 2. Save messages (after session exists in DB)
        greeting = ChatMessage(
            session_id=session_id,
            role='assistant',
            content='Hello! I am MediMind, your medical assistant. Please describe your symptoms or health concerns.',
            message_order=1
        )
        db.add(greeting)
        
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
        
    except IntegrityError as e:
        db.rollback()
        print(f"❌ Database integrity error: {e}")
        raise ValueError(f"Failed to save session: {e}")
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Database error: {e}")
        raise ValueError(f"Database error: {e}")
        
    finally:
        db.close()
    
    return str(session_id), reply, interview.finished


# =====================================================
# ✅ UPDATED: CHAT SESSION (with DB restore)
# =====================================================
def chat_session(session_id: str, user_message: str):
    if not _is_valid_uuid(session_id):
        raise ValueError("Invalid session_id")

    # ✅ NEW: Try to restore session from database if not in memory
    if session_id not in _sessions:
        db = SessionLocal()
        try:
            if not restore_session_from_db(session_id, db):
                raise ValueError("Session not found or has been completed. Please start a new chat.")
        finally:
            db.close()

    # 🔒 GUARDRAILS
    clean_input = sanitize_user_input(user_message)
    ensure_medical_scope(clean_input)

    session = _sessions[session_id]
    interview = session["interview"]
    message_count = session["message_count"]
    
    reply = interview.reply(clean_input)
    
    # 💾 Save messages to database
    db = SessionLocal()
    try:
        # Save user message
        user_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='user',
            content=user_message,
            message_order=message_count + 1
        )
        db.add(user_msg)
        
        # Save bot reply
        bot_msg = ChatMessage(
            session_id=uuid.UUID(session_id),
            role='assistant',
            content=reply,
            message_order=message_count + 2
        )
        db.add(bot_msg)
        
        # Update session timestamp
        db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id)
        ).update({"updated_at": datetime.utcnow()})
        
        db.commit()
        
        session["message_count"] = message_count + 2
        
    except IntegrityError as e:
        db.rollback()
        print(f"❌ Failed to save messages: {e}")
        # Continue without saving (better than crashing)
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Database error: {e}")
        
    finally:
        db.close()

    # 🔚 Interview finished
    if interview.finished:
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
            
            # 💾 Save assessment and mark session complete
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
                
                # Update session status
                db.query(ChatSession).filter(
                    ChatSession.session_id == uuid.UUID(session_id)
                ).update({
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                })
                
                db.commit()
                
            except IntegrityError as e:
                db.rollback()
                print(f"❌ Failed to save assessment: {e}")
                
            except SQLAlchemyError as e:
                db.rollback()
                print(f"❌ Database error: {e}")
                
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
    _sessions.pop(session_id, None)
