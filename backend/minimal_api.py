from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import os
import sys

app = FastAPI(title="Medical Interview Chatbot API", 
              description="API for the medical interview chatbot that simulates a doctor's consultation",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agents - initialized once
interview_agents = {}

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    finished: bool
    history: List[Message]

class ResetRequest(BaseModel):
    session_id: str

def dummy_retriever(query, top_k=5):
    """A dummy retriever that returns empty results to avoid ChromaDB issues"""
    return []

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    print("Starting up Medical Interview Chatbot API...")
    print("Using dummy retriever to bypass ChromaDB issues")
    
    # Test importing the LLM components
    try:
        # Add backend directory to path
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(backend_dir)
        
        from llm.interview_agent import MedicalInterviewAgent
        from llm.explanation_agent import MedicalExplanationAgent
        print("✓ LLM components loaded successfully")
        
    except Exception as e:
        print(f"✗ Error loading LLM components: {e}")
        import traceback
        traceback.print_exc()

@app.post("/start", response_model=ChatResponse)
async def start_interview(request: ChatRequest):
    """Start a new medical interview session"""
    try:
        # Add backend directory to path
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(backend_dir)
        
        # Import required modules
        from llm.interview_agent import MedicalInterviewAgent
        
        # Create a new interview agent for this session with dummy retriever
        interview_agent = MedicalInterviewAgent(dummy_retriever)
        interview_agents[request.session_id] = interview_agent
        
        # Get the initial response
        response = interview_agent.start(request.message)
        
        # Return the response with session info
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            finished=interview_agent.finished,
            history=[Message(role=msg["role"], content=msg["content"]) for msg in interview_agent.history]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")

@app.post("/reply", response_model=ChatResponse)
async def reply_to_interview(request: ChatRequest):
    """Continue an existing medical interview session"""
    try:
        # Check if session exists
        if request.session_id not in interview_agents:
            raise HTTPException(status_code=404, detail="Session not found. Please start a new interview.")
        
        # Get the interview agent for this session
        interview_agent = interview_agents[request.session_id]
        
        # Get the response
        response = interview_agent.reply(request.message)
        
        # Check if interview is finished
        finished = interview_agent.finished
        
        # If finished, generate explanation using the explanation agent
        if finished:
            try:
                # Import the explanation agent
                backend_dir = os.path.dirname(os.path.abspath(__file__))
                sys.path.append(backend_dir)
                from llm.explanation_agent import MedicalExplanationAgent
                
                # Create explanation agent with dummy retriever
                explanation_agent = MedicalExplanationAgent(dummy_retriever)
                
                # Generate explanation
                explanation = explanation_agent.explain(interview_agent.history)
                
                # Append explanation to response
                response += f"\n\nThank you. Here is a simple explanation:\n\n{explanation}"
            except Exception as exp_error:
                print(f"Error generating explanation: {exp_error}")
                import traceback
                traceback.print_exc()
                # Continue with original response if explanation fails
        
        # Return the response with session info
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            finished=finished,
            history=[Message(role=msg["role"], content=msg["content"]) for msg in interview_agent.history]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing reply: {str(e)}")

@app.post("/reset")
async def reset_interview(request: ResetRequest):
    """Reset an existing medical interview session"""
    try:
        # Remove the interview agent for this session if it exists
        if request.session_id in interview_agents:
            del interview_agents[request.session_id]
        
        return {"message": f"Session {request.session_id} has been reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Medical Interview Chatbot API is running"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the Medical Interview Chatbot API", 
        "docs": "/docs",
        "endpoints": {
            "POST /start": "Start a new medical interview",
            "POST /reply": "Continue an existing medical interview",
            "POST /reset": "Reset a medical interview session",
            "GET /health": "Health check"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)