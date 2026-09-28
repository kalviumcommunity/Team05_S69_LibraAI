"""
LibraAI - FastAPI Backend Application
Day 6 Upgrade: Real VectorRetriever wired to /query endpoint
Reference: PRD Appendix B, §8.2, §8.3, §8.5, FR-04, FR-05, FR-07, FR-10, FR-19, NFR-03
"""

import sys
import os

# Add repository root to python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from config.schema import QueryRequest, QueryResponse, Citation
from retrieval.retriever import VectorRetriever

app = FastAPI(
    title="LibraAI API",
    description="University Library Research Assistant — RAG Backend API",
    version="2.0.0",
)

# Enable CORS for local Streamlit frontend (default port 8501) or web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton retriever — loaded once at startup to avoid per-request model loading
_retriever: VectorRetriever | None = None


def get_retriever() -> VectorRetriever:
    """Lazily initialize and cache the VectorRetriever singleton."""
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness & readiness probe."""
    return {
        "status": "ok",
        "service": "LibraAI Backend",
        "version": "2.0.0",
        "stage": "Day 6 - Real Retrieval",
    }


@app.post("/query", response_model=QueryResponse, tags=["Retrieval & Generation"])
async def query_library(request: QueryRequest) -> QueryResponse:
    """
    Primary RAG query endpoint — Day 6 real-retrieval implementation.

    Workflow:
    1. Embed user query using DefaultEmbeddingFunction (all-MiniLM-L6-v2).
    2. Query ChromaDB collection for top-k semantically similar chunks.
    3. Evaluate cosine similarity against calibrated threshold (0.38).
    4. If below threshold → return refusal response with 0 citations (FR-05, FR-10).
    5. If above threshold → return answer preview and deduplicated citations (FR-07, NFR-03).
    """
    try:
        retriever = get_retriever()
        response = retriever.query(request)
        return response
    except Exception as exc:
        # Fail-safe: surface internal error without leaking implementation details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Retrieval service temporarily unavailable. Please try again.",
        ) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
