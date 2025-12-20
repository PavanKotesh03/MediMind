from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import chat, auth, history  # Add history
from guardrails.guard_exceptions import PromptInjectionError

app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend with Authentication",
    version="1.0.0"
)

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

# =====================================================
# ROUTERS
# =====================================================
app.include_router(chat.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(history.router, prefix="/api")  # NEW

@app.get("/")
def health_check():
    return {"status": "Medimind API running", "version": "1.0.0"}
