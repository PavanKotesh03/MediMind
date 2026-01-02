from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routers import chat, auth, history
from api.schemas.response import APIResponse
from guardrails.guard_exceptions import PromptInjectionError

# Preload heavy models on startup
from scripts.step4_query_system_hybrid import hybrid_search


# =====================================================
# LOGGING CONFIG
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# =====================================================
# FASTAPI APP
# =====================================================
app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend with Authentication",
    version="1.0.0"
)


# =====================================================
# STARTUP EVENT
# =====================================================
@app.on_event("startup")
async def preload_models():
    """Preload RAG models on app startup to avoid first-query delay"""
    logger.info("Starting model preload on app startup")
    try:
        hybrid_search("preload", top_k=1)
        logger.info("RAG models preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload models: {e}")


# =====================================================
# GLOBAL EXCEPTION HANDLER
# =====================================================
@app.exception_handler(PromptInjectionError)
async def prompt_injection_handler(request: Request, exc: PromptInjectionError):
    logger.warning(f"Prompt injection detected: {str(exc)}")

    return APIResponse(
        success=False,
        message="Unsafe input detected",
        error=str(exc)
    )


# =====================================================
# CORS & SESSION
# =====================================================
from starlette.middleware.sessions import SessionMiddleware
import os

# Session Middleware (Required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key"),
    max_age=3600  # 1 hour
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# ROUTERS
# =====================================================
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(history.router, prefix="/api/history", tags=["Chat History"])


# =====================================================
# HEALTH CHECK
# =====================================================
@app.get("/", response_model=APIResponse[dict])
def health_check():
    logger.debug("Health check requested")

    return APIResponse(
        success=True,
        message="Medimind API running",
        data={"version": "1.0.0"}
    )
