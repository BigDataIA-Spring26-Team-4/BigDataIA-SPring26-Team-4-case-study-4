"""
CS4 RAG & Search — FastAPI Application.

Separate API server for CS4 RAG capabilities:
- Evidence search (dense + sparse + hybrid)
- Score justification generation
- IC meeting preparation
- Analyst notes submission

Connects to CS1/CS2/CS3 via HTTP clients.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    log.info("cs4_startup", message="CS4 RAG & Search API starting")
    # TODO: Initialize ChromaDB, HybridRetriever, ModelRouter
    yield
    log.info("cs4_shutdown", message="CS4 RAG & Search API shutting down")


app = FastAPI(
    title="PE Org-AI-R CS4 — RAG & Search",
    version="1.0.0",
    description="Evidence retrieval and score justification for PE investment committees",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# CS4 Routers (will be added in Phase 4)
# ============================================================================
# from src.api import search, justification, analyst
# app.include_router(search.router)
# app.include_router(justification.router)
# app.include_router(analyst.router)


@app.get("/", tags=["root"])
async def root():
    """CS4 API root."""
    return {
        "name": "PE Org-AI-R CS4 — RAG & Search",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check."""
    return {"status": "healthy", "service": "cs4-rag-search"}
