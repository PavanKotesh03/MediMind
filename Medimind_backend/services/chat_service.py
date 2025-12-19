import uuid

from llm.interview_agent import MedicalInterviewAgent
from llm.explanation_agent import MedicalExplanationAgent
from llm.fact_extractor import extract_facts
from rules.disease_engine import DiseasePatternEngine
from scripts.step4_query_system_hybrid import hybrid_search

from guardrails.input_guard import sanitize_user_input
from guardrails.scope_guard import ensure_medical_scope


# =====================================================
# RAG RETRIEVER
# =====================================================
def retriever(query, top_k=5):
    results = hybrid_search(query)
    return [
        {
            "text": r["text"],
            "metadata": r.get("metadata", {})
        }
        for r in results[:top_k]
    ]


# =====================================================
# GLOBAL ENGINES
# =====================================================
disease_engine = DiseasePatternEngine()
explanation_agent = MedicalExplanationAgent(retriever)


# =====================================================
# IN-MEMORY SESSION STORE
# =====================================================
_sessions = {}


# =====================================================
# HELPERS
# =====================================================
def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False


# =====================================================
# START SESSION
# =====================================================
def start_session(user_message: str):
    # 🔒 GUARDRAILS (INPUT)
    clean_input = sanitize_user_input(user_message)
    ensure_medical_scope(clean_input)

    # ✅ Create interview FIRST
    interview = MedicalInterviewAgent(retriever)

    # ✅ Use CLEAN input only
    reply = interview.start(clean_input)

    session_id = str(uuid.uuid4())

    _sessions[session_id] = {
        "interview": interview,
        "final": None
    }

    return session_id, reply, interview.finished


# =====================================================
# CHAT SESSION
# =====================================================
def chat_session(session_id: str, user_message: str):
    if not _is_valid_uuid(session_id):
        raise ValueError("Invalid session_id")

    if session_id not in _sessions:
        raise ValueError("Session not found")

    # 🔒 GUARDRAILS (INPUT)
    clean_input = sanitize_user_input(user_message)
    ensure_medical_scope(clean_input)

    session = _sessions[session_id]
    interview = session["interview"]

    # ✅ Use CLEAN input
    reply = interview.reply(clean_input)

    # 🔚 Interview finished → FINAL OUTPUT
    if interview.finished:

        if session["final"] is None:

            # 1️⃣ Extract facts
            facts = extract_facts(interview.history)

            # 2️⃣ Rule engine
            matches = disease_engine.evaluate(facts)

            if matches:
                top = matches[0]
            else:
                top = {
                    "disease": "Undifferentiated Symptom Pattern",
                    "severity": "MEDIUM",
                    "reason": "Symptoms require further medical evaluation"
                }

            # 3️⃣ RAG explanation
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
    _sessions.pop(session_id, None)
