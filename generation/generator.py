"""
LibraAI - Grounded Answer Generation Module
Day 8 Deliverable: LLM-powered answer generation strictly grounded in retrieved context.
Reference: PRD §8.4, FR-11, FR-12, FR-13, NFR-03
"""

import os
import sys
import logging
from typing import List, Tuple, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.schema import ChunkMetadata, Citation, QueryRequest, QueryResponse
from retrieval.retriever import VectorRetriever, REFUSAL_MESSAGE

logger = logging.getLogger("libraai.generator")

# ── System prompt (Variant 2 from prompts.md — Concise Grounded Research Assistant) ──

SYSTEM_PROMPT = """You are LibraAI, a grounded university library research assistant.

Use only the supplied context chunks to answer the user's question.

Requirements:
- Do not use outside knowledge.
- Do not invent, guess, or fabricate facts.
- Do not invent or guess citations.
- Base every factual statement on the supplied context.
- If the answer cannot be supported by the context, say so instead of guessing.
- Answer concisely and directly.
- Include only information relevant to the question.
- Do not turn the retrieved context into a long document summary.
- After your answer, list the sources you used in a "Sources:" section using ONLY the document titles, page numbers, and sections provided in the chunk metadata. Do NOT invent source information."""


def _format_context(retrieved: List[Tuple[ChunkMetadata, float]], chunk_texts: List[str]) -> str:
    """
    Format retrieved chunks into a numbered context block for the LLM.
    Each chunk is labeled with its metadata so the LLM can attribute facts.
    """
    context_parts = []
    for i, ((meta, score), text) in enumerate(zip(retrieved, chunk_texts)):
        header = (
            f"[Chunk {i+1}] "
            f"Document: {meta.doc_title} | "
            f"Page: {meta.page_number} | "
            f"Section: {meta.section} | "
            f"Similarity: {score:.3f}"
        )
        context_parts.append(f"{header}\n{text}")
    return "\n\n---\n\n".join(context_parts)


def _generate_with_openai(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> str:
    """Generate answer using OpenAI API (requires OPENAI_API_KEY)."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def _generate_with_huggingface(system_prompt: str, user_prompt: str) -> str:
    """
    Fallback: Generate answer using HuggingFace Inference API (free tier).
    Uses Mistral-7B-Instruct or similar open model.
    Requires HF_TOKEN environment variable.
    """
    import requests

    hf_token = os.environ.get("HF_TOKEN", "")
    model_id = "mistralai/Mistral-7B-Instruct-v0.3"
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"

    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    prompt = f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.1,
            "return_full_text": False,
        },
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    result = resp.json()

    if isinstance(result, list) and len(result) > 0:
        return result[0].get("generated_text", "").strip()
    return str(result)


def _generate_offline_fallback(retrieved: List[Tuple[ChunkMetadata, float]], chunk_texts: List[str], question: str) -> str:
    """
    Zero-dependency offline fallback: returns a formatted extractive answer
    built directly from the top retrieved chunk, without any LLM call.
    Useful for testing and environments with no API access.
    """
    if not retrieved or not chunk_texts:
        return REFUSAL_MESSAGE

    top_meta, top_score = retrieved[0]
    top_text = chunk_texts[0]

    # Take first ~500 chars as the answer excerpt
    excerpt = top_text[:500].strip()
    if len(top_text) > 500:
        excerpt += "..."

    answer = (
        f"Based on the retrieved evidence:\n\n"
        f"{excerpt}\n\n"
        f"Sources:\n"
        f"- {top_meta.doc_title}, Page {top_meta.page_number} (Section: {top_meta.section})"
    )

    for meta, _ in retrieved[1:3]:
        answer += f"\n- {meta.doc_title}, Page {meta.page_number} (Section: {meta.section})"

    return answer


def generate_answer(
    question: str,
    retrieved: List[Tuple[ChunkMetadata, float]],
    chunk_texts: List[str],
    provider: Optional[str] = None,
) -> str:
    """
    Generate a grounded answer using the best available LLM provider.

    Args:
        question: The user's question.
        retrieved: List of (ChunkMetadata, similarity_score) tuples from the retriever.
        chunk_texts: List of chunk text strings, aligned with `retrieved`.
        provider: Force a specific provider ("openai", "huggingface", "offline").
                  If None, auto-detects based on available API keys.

    Returns:
        The generated answer string.
    """
    context = _format_context(retrieved, chunk_texts)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    # Auto-detect provider
    if provider is None:
        if os.environ.get("OPENAI_API_KEY") and not os.environ.get("OPENAI_API_KEY", "").startswith("sk-placeholder"):
            provider = "openai"
        elif os.environ.get("HF_TOKEN"):
            provider = "huggingface"
        else:
            provider = "offline"

    logger.info(f"Using generation provider: {provider}")

    try:
        if provider == "openai":
            return _generate_with_openai(SYSTEM_PROMPT, user_prompt)
        elif provider == "huggingface":
            return _generate_with_huggingface(SYSTEM_PROMPT, user_prompt)
        else:
            return _generate_offline_fallback(retrieved, chunk_texts, question)
    except Exception as e:
        logger.error(f"LLM generation failed ({provider}): {e}")
        logger.info("Falling back to offline extractive answer.")
        return _generate_offline_fallback(retrieved, chunk_texts, question)


class GroundedGenerator:
    """
    End-to-end RAG pipeline:
    Retrieval → Relevance Check → Grounded Generation → Citations.
    """

    def __init__(
        self,
        retriever: Optional[VectorRetriever] = None,
        provider: Optional[str] = None,
    ):
        self.retriever = retriever or VectorRetriever()
        self.provider = provider

    def query(self, request: QueryRequest) -> QueryResponse:
        """Retrieve evidence, generate an answer, and return citations."""

        # Step 1: Retrieve relevant chunks
        retrieved = self.retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            course_code=request.course_code,
            doc_type=request.doc_type,
        )

        # Step 2: Check relevance
        is_relevant, confidence = self.retriever.evaluate_relevance(retrieved)

        if not is_relevant:
            logger.info(
                "Query refused (confidence %.3f): %s",
                confidence,
                request.query[:60],
            )
            return QueryResponse(
                answer=REFUSAL_MESSAGE,
                citations=[],
                refused=True,
                confidence_score=round(confidence, 4),
            )

        # Step 3: Retrieve the actual text for each chunk
        collection = self.retriever.collection
        chunk_ids = [meta.chunk_id for meta, _ in retrieved]

        try:
            results = collection.get(
                ids=chunk_ids,
                include=["documents"],
            )

            id_to_text = {}
            if results and results.get("ids"):
                documents = results.get("documents") or []
                for chunk_id, document in zip(results["ids"], documents):
                    id_to_text[chunk_id] = document or ""

            chunk_texts = [
                id_to_text.get(chunk_id, "")
                for chunk_id in chunk_ids
            ]

        except Exception as e:
            logger.error("Failed to retrieve chunk texts: %s", e)
            chunk_texts = ["" for _ in retrieved]

        # Step 4: Generate the grounded answer
        answer = generate_answer(
            question=request.query,
            retrieved=retrieved,
            chunk_texts=chunk_texts,
            provider=self.provider,
        )

        # Step 5: Build citations with actual source text
        citations = []

        for (meta, _), chunk_text in zip(retrieved, chunk_texts):
            citations.append(
                Citation(
                    doc_title=meta.doc_title,
                    section=meta.section,
                    page_number=meta.page_number,
                    source_path=meta.source_path,
                    chunk_id=meta.chunk_id,
                    chunk_text=chunk_text,
                )
            )

        # Step 6: Return the answer and citations
        document_count = len({
            citation.doc_title for citation in citations
        })

        return QueryResponse(
            answer=answer,
            citations=citations,
            refused=False,
            confidence_score=round(confidence, 4),
            source_document_count=document_count,
        )
    