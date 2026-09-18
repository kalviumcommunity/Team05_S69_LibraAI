"""
LibraAI - FastAPI Backend Application
Day 2 Scaffold: API Contract & Stub Query Endpoint
Reference: PRD Appendix B, §8.2, §8.3, FR-19, NFR-03
"""

import sys
import os

# Add repository root to python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from config.schema import QueryRequest, QueryResponse, Citation

app = FastAPI(
    title="LibraAI API",
    description="University Library Research Assistant — RAG Backend API",
    version="1.0.0",
)

# Enable CORS for local Streamlit frontend (default port 8501) or web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness & readiness probe."""
    return {
        "status": "ok",
        "service": "LibraAI Backend",
        "version": "1.0.0",
        "stage": "Day 2 - Mock Contract",
    }


@app.post("/query", response_model=QueryResponse, tags=["Retrieval & Generation"])
async def query_library(request: QueryRequest) -> QueryResponse:
    """
    Primary RAG query endpoint.
    Day 2 Stub Implementation: returns a verified mock response adhering to
    the locked QueryResponse schema contract (FR-19, Appendix B).
    """
    query_lower = request.query.lower()

    # Stub simulation: Out-of-corpus queries trigger refusal path (FR-05, FR-10)
    out_of_corpus_triggers = ["shor", "bastille", "crispr", "quantum", "dna", "french revolution", "unknown"]
    if any(trigger in query_lower for trigger in out_of_corpus_triggers):
        return QueryResponse(
            answer="I don't know / not covered in the available materials.",
            citations=[],
            refused=True,
            confidence_score=0.25,
        )

    # In-corpus mock response grounded in Day 1 inspection of DOC-01
    return QueryResponse(
        answer=(
            "According to the study on password reuse, 34 out of 50 participants had at least one pair "
            "of reused passwords, and virtually all participants who reused passwords verbatim stated "
            "they did so for memorability reasons."
        ),
        citations=[
            Citation(
                doc_title="How Users Choose and Reuse Passwords",
                section="V. Password Extraction and Reuse",
                page_number=14,
                source_path="data/doc01_password_reuse_research_paper.pdf",
                chunk_id="doc01_password_reuse_p14_c002",
            )
        ],
        refused=False,
        confidence_score=0.92,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
