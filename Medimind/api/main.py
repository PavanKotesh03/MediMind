from fastapi import FastAPI
from api.routers import chat

app = FastAPI(
    title="Medimind API",
    description="Medical Interview & Rule-Engine Guided Explanation Backend",
    version="1.0.0"
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
