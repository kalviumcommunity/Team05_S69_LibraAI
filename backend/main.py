"""
LibraAI - FastAPI Backend Application
Day 7: Retrieval-Augmented Generation with Gemini
"""

import logging
import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from config.schema import QueryRequest, QueryResponse
from generation.llm import GeminiGenerator, REFUSAL_MESSAGE
from retrieval.retriever import VectorRetriever

logger = logging.getLogger("libraai.backend")

app = FastAPI(
    title="LibraAI API",
    description="University Library Research Assistant — RAG Backend API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_retriever = None
_generator = None


def get_retriever() -> VectorRetriever:
    global _retriever

    if _retriever is None:
        _retriever = VectorRetriever()

    return _retriever


def get_generator() -> GeminiGenerator:
    global _generator

    if _generator is None:
        _generator = GeminiGenerator()

    return _generator


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "LibraAI Backend",
        "version": "2.0.0",
        "stage": "Day 6 - Real Retrieval",
    }


@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["Retrieval & Generation"],
)
async def query_library(request: QueryRequest) -> QueryResponse:
    try:
        retriever = get_retriever()

        retrieved = retriever.retrieve_with_text(
            query=request.query,
            top_k=request.top_k,
            course_code=request.course_code,
            doc_type=request.doc_type,
        )

        metadata_scores = [
            (metadata, score)
            for _, metadata, score in retrieved
        ]

        is_relevant, confidence = retriever.evaluate_relevance(
            metadata_scores
        )

        if not is_relevant:
            logger.info(
                "Query refused (confidence %.3f): %s",
                confidence,
                request.query[:50],
            )

            return QueryResponse(
                answer=REFUSAL_MESSAGE,
                citations=[],
                refused=True,
                confidence_score=round(confidence, 4),
            )

        context = "\n\n".join(
            (
                f"[Source {index}]\n"
                f"Document: {metadata.doc_title}\n"
                f"Section: {metadata.section}\n"
                f"Page: {metadata.page_number}\n"
                f"Content:\n{chunk_text}"
            )
            for index, (chunk_text, metadata, _) in enumerate(
                retrieved,
                start=1,
            )
        )

        generator = get_generator()

        answer = generator.generate_answer(
            question=request.query,
            context=context,
        )

        if answer.strip().casefold() == REFUSAL_MESSAGE.casefold():
            return QueryResponse(
                answer=REFUSAL_MESSAGE,
                citations=[],
                refused=True,
                confidence_score=round(confidence, 4),
            )

        citations = retriever.get_citations(metadata_scores)

        return QueryResponse(
            answer=answer,
            citations=citations,
            refused=False,
            confidence_score=round(confidence, 4),
        )

    except Exception as exc:
        logger.exception("Error processing library query")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The query could not be processed. Please try again.",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )