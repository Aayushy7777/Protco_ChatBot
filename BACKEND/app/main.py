"""
FastAPI application entry point.
Production-grade API with OpenClaw agent orchestration and RAG support.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.services import get_agent
from app.models import ChatRequest, ChatResponse, HealthResponse

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ─────────────────────── Lifespan Events ──────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("🚀 CSV Chat Agent API starting...")
    logger.info(f"Environment: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"Vector Store: {settings.VECTOR_STORE_TYPE} at {settings.CHROMA_PERSIST_DIR}")

    # Initialize agent (loads models)
    agent = get_agent()
    logger.info("✅ OpenClaw Agent initialized")

    yield

    logger.info("🛑 Shutting down...")


# ─────────────────────── FastAPI App ──────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade CSV analysis API with RAG and OpenClaw agent orchestration",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────── Routes ──────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        ollama_status="ready",
        vector_store_status="ready",
        message="CSV Chat Agent is operational",
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Accepts user message and routes through OpenClaw agent pipeline.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        agent = get_agent()
        result = await agent.run(
            message=request.message,
            active_file=request.active_file,
            all_files=request.all_files,
            conversation_history=request.conversation_history,
            session_id=request.session_id,
        )

        return ChatResponse(
            intent=result.intent,
            answer=result.answer,
            chart_config=result.chart_config,
            dashboard_config=result.dashboard_config,
            table_data=result.table_data or [],
            table_columns=result.table_columns or [],
            active_file=result.active_file,
            error=result.error,
            context_used=result.context_used,
        )

    except Exception as e:
        logger.exception(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_files(files: list):
    """File upload endpoint (placeholder)."""
    return {"status": "ok", "message": "Upload endpoint not yet implemented"}


# ─────────────────────── Root ──────────────────────────

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
