"""
Main entry point for the Medical Interview Chatbot API V2.
This is the production-ready version with modular structure.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from services.chat_service import initialize_services
from routes.chat_routes import router as chat_router
from routes.system_routes import router as system_router

# Create FastAPI app
app = FastAPI(
    title="Medical Interview Chatbot API V2",
    description="Production-ready API for the medical interview chatbot with modular structure",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system_router)
app.include_router(chat_router)

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    success = initialize_services()
    if success:
        print("✅ API V2 startup completed successfully")
    else:
        print("⚠️ API V2 startup completed with fallback components")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)