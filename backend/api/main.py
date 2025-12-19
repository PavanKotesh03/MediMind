from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import chat, auth  # Both routers
from guardrails.guard_exceptions import PromptInjectionError

app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend with Authentication",
    version="1.0.0"
)

# =====================================================
# EXCEPTION HANDLER (GUARDRAILS)
# =====================================================
@app.exception_handler(PromptInjectionError)
async def prompt_injection_handler(request: Request, exc: PromptInjectionError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Unsafe input detected",
            "message": str(exc)
        }
    )

# =====================================================
# CORS MIDDLEWARE
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ROUTERS
# =====================================================
app.include_router(chat.router, prefix="/api")      # Chat routes with guardrails
app.include_router(auth.router, prefix="/api")      # Authentication routes

# =====================================================
# HEALTH CHECK
# =====================================================
@app.get("/")
def health_check():
    return {"status": "Medimind API running", "version": "1.0.0"}
