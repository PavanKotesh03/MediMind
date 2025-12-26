import subprocess
import os
import threading
import time
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import chat, auth, history
from guardrails.guard_exceptions import PromptInjectionError

app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend with Authentication",
    version="1.0.0"
)

# =====================================================
# OLLAMA AUTO-MANAGEMENT (llama3.1:8b ONLY)
# =====================================================
def start_ollama():
    """Start Ollama server if not running"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        print("Ollama already running")
        return True
    except:
        print("Starting Ollama server...")
        if os.name == 'nt':  # Windows
            subprocess.Popen([
                "ollama", "serve"
            ], stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW)
        else:  # Linux/Mac
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        
        # Wait for startup
        for i in range(15):
            try:
                requests.get(f"{ollama_url}/api/tags", timeout=3)
                print("Ollama started successfully")
                return True
            except:
                time.sleep(2)
        print("Warning: Ollama startup delayed")
        return False

def warm_llama_model():
    """Pre-warm llama3.1:8b - ELIMINATES first response delay"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3.1:8b")
    
    print(f"Warming up {model_name}...")
    
    # 1. Ensure model is loaded
    try:
        requests.post(f"{ollama_url}/api/chat",
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "preload medical knowledge"}],
                "options": {"num_predict": 50},
                "stream": False
            },
            timeout=90
        )
        print(f"{model_name} warmed - First response INSTANT")
    except Exception as e:
        print(f"Warning: Model warmup failed: {e}")

def keep_model_active():
    """Keep llama3.1:8b in VRAM - continuous pings"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3.1:8b")
    
    while True:
        time.sleep(45)  # Ping every 45s
        try:
            requests.get(f"{ollama_url}/api/tags", timeout=5)
        except:
            pass  # Silent fail

# =====================================================
# FASTAPI STARTUP - SINGLE COMMAND EVERYTHING
# =====================================================
@app.on_event("startup")
async def startup_event():
    # Thread 1: Start Ollama server
    ollama_ready = threading.Thread(target=start_ollama, daemon=True)
    ollama_ready.start()
    time.sleep(3)  # Give startup time
    
    # Thread 2: Warm llama3.1:8b model
    model_warm = threading.Thread(target=warm_llama_model, daemon=True)
    model_warm.start()
    
    # Thread 3: Keep model active forever
    keep_alive = threading.Thread(target=keep_model_active, daemon=True)
    keep_alive.start()
    
    print("Medimind FULLY READY (Ollama + llama3.1:8b warm)")
    print("Frontend: http://localhost:4200")
    print("Swagger: http://localhost:8000/docs")

@app.exception_handler(PromptInjectionError)
async def prompt_injection_handler(request: Request, exc: PromptInjectionError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Unsafe input detected",
            "message": str(exc)
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTERS
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(history.router, prefix="/api/history", tags=["Chat History"])

@app.get("/")
def health_check():
    return {"status": "Medimind API running", "version": "1.0.0"}
