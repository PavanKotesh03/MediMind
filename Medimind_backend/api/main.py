from fastapi import FastAPI, Request
from api.routers import chat
from guardrails.guard_exceptions import PromptInjectionError
from fastapi.responses import JSONResponse


app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend",
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



# =====================================================
# ROUTERS
# =====================================================
app.include_router(chat.router, prefix="/api")

# =====================================================
# HEALTH CHECK
# =====================================================
@app.get("/")
def health_check():
    return {"status": "Medimind API running"}
