"""
LibraAI - FastAPI Backend Application
Day 8 Upgrade: Grounded Generation wired to /query endpoint
Reference: PRD Appendix B, §8.2, §8.3, §8.4, §8.5, FR-04–FR-13, FR-19, NFR-03
"""

import sys
import os

# Add repository root to python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from config.schema import QueryRequest, QueryResponse, Citation
from generation.generator import GroundedGenerator

app = FastAPI(
    title="LibraAI API",
    description="University Library Research Assistant — RAG Backend API",
    version="3.0.0",
)

# Enable CORS for local Streamlit frontend (default port 8501) or web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton generator — loaded once at startup to avoid per-request model loading
_generator: GroundedGenerator | None = None


def get_generator() -> GroundedGenerator:
    """Lazily initialize and cache the GroundedGenerator singleton."""
    global _generator
    if _generator is None:
        _generator = GroundedGenerator()
    return _generator


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness & readiness probe."""
    return {
        "status": "ok",
        "service": "LibraAI Backend",
        "version": "3.0.0",
        "stage": "Day 8 - Grounded Generation",
    }


@app.post("/query", response_model=QueryResponse, tags=["Retrieval & Generation"])
async def query_library(request: QueryRequest) -> QueryResponse:
    """
    Primary RAG query endpoint — Day 8 grounded-generation implementation.

    Workflow:
    1. Embed user query and retrieve top-k semantically similar chunks.
    2. Evaluate cosine similarity against calibrated threshold (0.38).
    3. If below threshold → return refusal response with 0 citations (FR-05, FR-10).
    4. If above threshold → generate grounded LLM answer and return with citations.
    """
    try:
        generator = get_generator()
        response = generator.query(request)
        return response
    except Exception as exc:
        # Fail-safe: surface internal error without leaking implementation details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generation service temporarily unavailable. Please try again.",
        ) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

