from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

from api.routers import chat, auth, history  # Make sure history is imported
from guardrails.guard_exceptions import PromptInjectionError

# Preload heavy models on startup
from scripts.step4_query_system_hybrid import hybrid_search

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend with Authentication",
    version="1.0.0"
)
from guardrails.guard_exceptions import PromptInjectionError

# Preload heavy models on startup
from scripts.step4_query_system_hybrid import hybrid_search

app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend with Authentication",
    version="1.0.0"
)

@app.on_event("startup")
async def preload_models():
    """Preload RAG models on app startup to avoid first-query delay"""
    logger.info("Starting model preload on app startup")
    try:
        # Dummy search to load models
        hybrid_search("preload", top_k=1)
        logger.info("RAG models preloaded successfully")
        print("RAG models preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload models: {e}")
        print(f"Warning: Failed to preload models: {e}")

@app.exception_handler(PromptInjectionError)
async def prompt_injection_handler(request: Request, exc: PromptInjectionError):
    logger.warning(f"Prompt injection detected: {str(exc)}")
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

# =====================================================
# ROUTERS - FIXED PREFIXES
# =====================================================
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(history.router, prefix="/api/history", tags=["Chat History"])  # MUST BE /api/history

@app.get("/")
def health_check():
    logger.debug("Health check requested")
    return {"status": "Medimind API running", "version": "1.0.0"}
