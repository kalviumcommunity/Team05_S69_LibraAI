
"""
LibraAI - FastAPI Backend Application
Day 8: RAG Integration, Multi-topic Retrieval and Source Evidence
NVIDIA API Integration
"""

import logging
import os
import re
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from openai import APIConnectionError, APIStatusError, APITimeoutError

from config.schema import Citation, QueryRequest, QueryResponse
from generation.llm import NVIDIAGenerator, REFUSAL_MESSAGE
from retrieval.retriever import VectorRetriever


logging.basicConfig(level=logging.INFO)
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


def get_generator() -> NVIDIAGenerator:
    global _generator

    if _generator is None:
        _generator = NVIDIAGenerator()

    return _generator


def split_query_topics(query: str) -> list[str]:
    """
    Split a simple multi-topic question at the word 'and'.

    For example:
    'What do the materials say about password reuse and Spix's macaw?'

    becomes two searches:
    - 'What do the materials say about password reuse'
    - 'Spix's macaw'
    """
    parts = re.split(r"\band\b", query, flags=re.IGNORECASE)

    topics = [
        part.strip(" ,?.!")
        for part in parts
        if part.strip(" ,?.!")
    ]

    return topics or [query.strip()]


def build_citations(retrieved) -> list[Citation]:
    """
    Build citations with their actual retrieved chunk text.
    Duplicate document/page/section combinations are removed.
    """
    citations = []
    seen = set()

    for chunk_text, metadata, _ in retrieved:
        key = (
            metadata.doc_title,
            metadata.page_number,
            metadata.section,
        )

        if key in seen:
            continue

        seen.add(key)

        citations.append(
            Citation(
                doc_title=metadata.doc_title,
                section=metadata.section,
                page_number=metadata.page_number,
                source_path=metadata.source_path,
                chunk_id=metadata.chunk_id,
                chunk_text=chunk_text,
            )
        )

    return citations


def count_source_documents(citations: list[Citation]) -> int:
    """Count distinct documents represented by the citations."""
    return len({citation.doc_title for citation in citations})


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "LibraAI Backend",
        "version": "2.0.0",
        "stage": "Day 8 - RAG Integration",
    }


@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["Retrieval & Generation"],
)
async def query_library(request: QueryRequest) -> QueryResponse:
    try:
        # 1. Split the question into searchable topics.
        topics = split_query_topics(request.query)

        logger.info("Query topics: %s", topics)

        # 2. Retrieve evidence independently for each topic.
        retriever = get_retriever()

        retrieved = retriever.retrieve_for_topics(
            topics=topics,
            top_k=request.top_k,
            course_code=request.course_code,
            doc_type=request.doc_type,
        )

        # 3. Evaluate the relevance of the merged results.
        metadata_scores = [
            (metadata, score)
            for _, metadata, score in retrieved
        ]

        is_relevant, confidence = retriever.evaluate_relevance(
            metadata_scores
        )

        # 4. Refuse if no relevant evidence is found.
        if not is_relevant:
            logger.info(
                "Query refused by retrieval (confidence %.3f): %s",
                confidence,
                request.query[:100],
            )

            return QueryResponse(
                answer=REFUSAL_MESSAGE,
                citations=[],
                refused=True,
                confidence_score=round(confidence, 4),
                source_document_count=0,
            )

        # 5. Build context from all retrieved chunks.
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

        # 6. Generate the answer using NVIDIA.
        generator = get_generator()

        answer = generator.generate_answer(
            question=request.query,
            context=context,
        )

        # 7. Handle model refusal.
        if answer.strip().casefold() == REFUSAL_MESSAGE.casefold():
            logger.info(
                "NVIDIA refused query due to insufficient evidence: %s",
                request.query[:100],
            )

            return QueryResponse(
                answer=REFUSAL_MESSAGE,
                citations=[],
                refused=True,
                confidence_score=round(confidence, 4),
                source_document_count=0,
            )

        # 8. Build citations and count contributing documents.
        citations = build_citations(retrieved)
        document_count = count_source_documents(citations)

        logger.info(
            "Query answered successfully. Topics: %d, "
            "Sources: %d, confidence: %.3f",
            len(topics),
            document_count,
            confidence,
        )

        return QueryResponse(
            answer=answer,
            citations=citations,
            refused=False,
            confidence_score=round(confidence, 4),
            source_document_count=document_count,
        )

    # NVIDIA connection errors
    except (APITimeoutError, APIConnectionError) as exc:
        logger.exception("NVIDIA API connection or timeout error")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The NVIDIA AI service is temporarily unavailable. "
                "Please try again shortly."
            ),
        ) from exc

    # NVIDIA API errors, including authentication and model errors
    except APIStatusError as exc:
        logger.error(
            "NVIDIA API error: status=%s, response=%s",
            exc.status_code,
            exc.response.text,
        )

        if exc.status_code == 429:
            error_status = status.HTTP_429_TOO_MANY_REQUESTS
            detail = (
                "The NVIDIA API rate limit has been reached. "
                "Please try again later."
            )
        elif exc.status_code >= 500:
            error_status = status.HTTP_503_SERVICE_UNAVAILABLE
            detail = (
                "The NVIDIA AI service is temporarily unavailable. "
                "Please try again shortly."
            )
        else:
            error_status = status.HTTP_502_BAD_GATEWAY
            detail = (
                f"The NVIDIA API rejected the request "
                f"(HTTP {exc.status_code}). "
                "Check the backend logs for details."
            )

        raise HTTPException(
            status_code=error_status,
            detail=detail,
        ) from exc

    # Preserve intentional HTTP errors
    except HTTPException:
        raise

    # Unexpected application errors
    except Exception as exc:
        logger.exception("Error processing library query")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The query could not be processed. "
                "Please check the backend logs."
            ),
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )   