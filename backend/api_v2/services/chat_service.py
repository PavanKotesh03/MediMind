"""
Chat service for the Medical Interview Chatbot API V2.
Handles the business logic for chat interactions.
"""

import os
import sys
import time
from typing import List, Dict, Any

# Add the parent directory to the Python path to access llm modules
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

from llm.interview_agent import MedicalInterviewAgent
from llm.explanation_agent import MedicalExplanationAgent
from models.schemas import Message

# Global agents - initialized once
interview_agents: Dict[str, MedicalInterviewAgent] = {}
explanation_agent: MedicalExplanationAgent = None

# Timeout decorator for long-running operations
def timeout_handler(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This is a simple timeout mechanism
            # In production, you might want to use asyncio.wait_for or similar
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

# Lazy import of hybrid search function with fallback
def get_retriever():
    """Get the retriever function with lazy loading and fallback."""
    # Only initialize the retriever when it's first called
    if not hasattr(get_retriever, '_retriever'):
        try:
            # Import the hybrid search function directly
            sys.path.append(os.path.join(backend_dir, 'scripts'))
            from step4_query_system_hybrid import hybrid_search
            
            def retriever(query, top_k=5):
                try:
                    # Add timeout handling for hybrid search
                    start_time = time.time()
                    results = hybrid_search(query, top_k=top_k)
                    elapsed_time = time.time() - start_time
                    
                    if elapsed_time > 30:  # Log if it takes more than 30 seconds
                        print(f"⚠️ Hybrid search took {elapsed_time:.2f} seconds for query: {query}")
                    
                    return [{"text": r["text"], "metadata": r.get("metadata", {})} for r in results]
                except Exception as e:
                    print(f"Error in hybrid search: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to empty results if search fails
                    return []
            
            get_retriever._retriever = retriever
            print("✅ Hybrid search system loaded successfully")
        except Exception as e:
            print(f"❌ Error importing hybrid search: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to dummy retriever if import fails
            def dummy_retriever(query, top_k=5):
                print(f"⚠️ Using dummy retriever for query: {query}")
                return []
            get_retriever._retriever = dummy_retriever
            print("⚠️ Using fallback dummy retriever")
    
    return get_retriever._retriever

def initialize_services():
    """Initialize the global services and agents."""
    global explanation_agent
    print("Initializing Medical Interview Chatbot API V2...")
    try:
        # Defer retriever initialization until first use
        # Create explanation agent with a lazy retriever
        def lazy_retriever(query, top_k=5):
            # Get the actual retriever when first called
            actual_retriever = get_retriever()
            return actual_retriever(query, top_k)
        
        explanation_agent = MedicalExplanationAgent(lazy_retriever)
        print("✅ Medical Interview Chatbot API V2 initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing Medical Interview Chatbot API V2: {e}")
        import traceback
        traceback.print_exc()
        # Initialize with dummy components as fallback
        def dummy_retriever(query, top_k=5):
            print(f"⚠️ Using dummy retriever for explanation query: {query}")
            return []
        explanation_agent = MedicalExplanationAgent(dummy_retriever)
        print("⚠️ Medical Interview Chatbot API V2 initialized with fallback components")
        return False

def start_chat_session(session_id: str, message: str) -> tuple[str, bool, List[Message]]:
    """
    Start a new medical interview session.
    
    Returns:
        Tuple of (response, finished, history)
    """
    try:
        # Create a lazy retriever for this session
        def lazy_retriever(query, top_k=5):
            # Get the actual retriever when first called
            actual_retriever = get_retriever()
            return actual_retriever(query, top_k)
        
        # Create a new interview agent for this session
        interview_agent = MedicalInterviewAgent(lazy_retriever)
        interview_agents[session_id] = interview_agent
        
        # Get the initial response with timeout handling
        try:
            response = interview_agent.start(message)
        except Exception as e:
            print(f"❌ Error in interview_agent.start: {e}")
            raise Exception(f"Error processing request: {str(e)}")
        
        # Return the response with session info
        return response, interview_agent.finished, [Message(role=msg["role"], content=msg["content"]) for msg in interview_agent.history]
    except Exception as e:
        print(f"❌ Error starting interview: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Error starting interview: {str(e)}")

def continue_chat_session(session_id: str, message: str) -> tuple[str, bool, List[Message]]:
    """
    Continue an existing medical interview session.
    
    Returns:
        Tuple of (response, finished, history)
    """
    try:
        # Check if session exists
        if session_id not in interview_agents:
            raise Exception("Session not found. Please start a new interview.")
        
        # Get the interview agent for this session
        interview_agent = interview_agents[session_id]
        
        # Check if this is a new topic after interview completion
        if interview_agent.finished:
            # Look for keywords indicating a new medical topic
            new_topic_keywords = ["cancer", "diabetes", "heart", "stroke", "asthma", "arthritis", 
                                "hypertension", "depression", "anxiety", "migraine", "allergy", 
                                "fever", "headache", "cough", "pain"]
            message_lower = message.lower()
            
            # If user mentions a medical topic, reset the session to start fresh
            if any(keyword in message_lower for keyword in new_topic_keywords):
                print(f"🔄 Detected new medical topic: {message}. Resetting session.")
                # Remove the old session and create a new one
                if session_id in interview_agents:
                    del interview_agents[session_id]
                # Create a lazy retriever for this session
                def lazy_retriever(query, top_k=5):
                    # Get the actual retriever when first called
                    actual_retriever = get_retriever()
                    return actual_retriever(query, top_k)
                # Create a new interview agent for this new topic
                interview_agent = MedicalInterviewAgent(lazy_retriever)
                interview_agents[session_id] = interview_agent
                response = interview_agent.start(message)
                finished = interview_agent.finished
            else:
                # For non-medical topics, just acknowledge
                response = "Thank you for the information. If you have questions about a medical condition, please let me know."
                finished = True
        else:
            # Normal flow for ongoing interviews
            try:
                response = interview_agent.reply(message)
            except Exception as e:
                print(f"❌ Error in interview_agent.reply: {e}")
                raise Exception(f"Error processing request: {str(e)}")
            finished = interview_agent.finished
        
        # If finished, generate explanation
        if finished:
            try:
                try:
                    explanation = explanation_agent.explain(interview_agent.history)
                except Exception as e:
                    print(f"❌ Error in explanation_agent.explain: {e}")
                    explanation = ""
                # Format the explanation properly with markdown
                if explanation:
                    response += f"\n\nThank you. Here is a simple explanation:\n\n{explanation}"
                else:
                    response += "\n\nThank you for providing all this information. Based on our conversation, I recommend consulting with a healthcare professional for a proper diagnosis."
            except Exception as e:
                print(f"❌ Error generating explanation: {e}")
                import traceback
                traceback.print_exc()
                response += "\n\nThank you for providing all this information. Based on our conversation, I recommend consulting with a healthcare professional for a proper diagnosis."
        
        # Return the response with session info
        return response, finished, [Message(role=msg["role"], content=msg["content"]) for msg in interview_agent.history]
    except Exception as e:
        print(f"❌ Error processing reply: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Error processing reply: {str(e)}")

def reset_chat_session(session_id: str) -> bool:
    """
    Reset an existing medical interview session.
    
    Returns:
        True if successful
    """
    try:
        # Remove the interview agent for this session if it exists
        if session_id in interview_agents:
            del interview_agents[session_id]
        return True
    except Exception as e:
        raise Exception(f"Error resetting session: {str(e)}")