"""
PIA — Placement Intelligence Assistant
FastAPI Application Entry Point

Configures CORS, registers routes, and manages application lifecycle.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from backend.config import settings
from backend.api.routes import router


# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)
logger.add(
    "logs/pia_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown events."""
    # --- Startup ---
    logger.info("=" * 60)
    logger.info("PIA — Placement Intelligence Assistant")
    logger.info("=" * 60)
    logger.info(f"LLM Model: {settings.llm_model}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info(f"Reranker Model: {settings.reranker_model}")
    logger.info(f"ChromaDB Path: {settings.chroma_persist_dir}")
    logger.info(f"Data Directory: {settings.data_dir}")

    # Pre-initialize vector store (loads embedding model)
    try:
        from backend.db.vector_store import vector_store
        vector_store.initialize()
        logger.info(f"Vector store initialized: {vector_store.get_stats()}")
    except Exception as e:
        logger.warning(f"Vector store initialization deferred: {e}")

    yield

    # --- Shutdown ---
    logger.info("PIA shutting down...")


# Create FastAPI app
app = FastAPI(
    title="PIA — Placement Intelligence Assistant",
    description=(
        "AI-powered placement preparation platform with hybrid RAG pipeline. "
        "Analyze JDs, retrieve interview experiences, and get cited answers."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PIA"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
