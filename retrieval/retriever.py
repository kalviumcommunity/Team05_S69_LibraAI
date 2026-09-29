
"""
LibraAI - Semantic Retrieval & Relevance Thresholding Module
Day 8: Multi-topic retrieval with source evidence
"""

import logging
import os
import re
import sys
from typing import Optional, List, Dict, Any, Tuple

import chromadb

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from config.schema import ChunkMetadata, Citation, QueryRequest, QueryResponse
from indexing.indexer import (
    get_chroma_client,
    get_or_create_collection,
    get_embedding_function,
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION_NAME,
)

logger = logging.getLogger("libraai.retriever")

# Calibrated relevance threshold:
# In-corpus benchmark queries score between 0.41 and 0.82
# Out-of-corpus queries score between 0.11 and 0.34
DEFAULT_RELEVANCE_THRESHOLD = 0.35
REFUSAL_MESSAGE = "I don't know / not covered in the available materials."


class VectorRetriever:
    """
    Semantic search engine over the indexed LibraAI ChromaDB corpus.

    Supports:
    - Semantic retrieval
    - Metadata filtering
    - Relevance thresholding
    - Multi-topic retrieval
    - Deduplication
    - Source citations
    """

    def __init__(
        self,
        persist_dir: str = DEFAULT_CHROMA_DIR,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        embedding_fn=None,
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.relevance_threshold = relevance_threshold
        self.embedding_fn = embedding_fn or get_embedding_function()
        self.client = get_chroma_client(persist_dir)
        self.collection = get_or_create_collection(
            self.client,
            collection_name,
            self.embedding_fn,
        )

    def _build_filter(
        self,
        course_code: Optional[str],
        doc_type: Optional[str],
        exclude_references: bool,
    ) -> Optional[Dict[str, Any]]:
        filters = []

        if exclude_references:
            filters.append({"is_reference": False})

        if course_code:
            filters.append({"course_code": course_code})

        if doc_type:
            filters.append({"doc_type": doc_type})

        if len(filters) == 1:
            return filters[0]

        if len(filters) > 1:
            return {"$and": filters}

        return None

    def _query_collection(
        self,
        query: str,
        top_k: int,
        course_code: Optional[str],
        doc_type: Optional[str],
        exclude_references: bool,
    ) -> Dict[str, Any]:
        where_clause = self._build_filter(
            course_code,
            doc_type,
            exclude_references,
        )

        query_kwargs: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": top_k,
        }

        if where_clause:
            query_kwargs["where"] = where_clause

        return self.collection.query(**query_kwargs)

    @staticmethod
    def _chunk_key(
        text: str,
        metadata: ChunkMetadata,
    ) -> tuple:
        """Create a stable key for deduplicating retrieved chunks."""
        if metadata.chunk_id:
            return ("chunk_id", metadata.chunk_id)

        return (
            "content",
            metadata.doc_title,
            metadata.page_number,
            metadata.section,
            text,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        course_code: Optional[str] = None,
        doc_type: Optional[str] = None,
        exclude_references: bool = True,
    ) -> List[Tuple[ChunkMetadata, float]]:
        """
        Retrieve chunks as (ChunkMetadata, similarity_score) tuples.
        This format is preserved for backward compatibility.
        """
        try:
            results = self._query_collection(
                query,
                top_k,
                course_code,
                doc_type,
                exclude_references,
            )
        except Exception:
            logger.exception("Error executing Chroma query")
            return []

        retrieved = []

        if (
            not results
            or not results.get("documents")
            or not results["documents"][0]
        ):
            return retrieved

        metadatas = (
            results["metadatas"][0]
            if results.get("metadatas")
            else []
        )
        distances = (
            results["distances"][0]
            if results.get("distances")
            else []
        )

        for i, _ in enumerate(results["documents"][0]):
            meta_dict = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 1.0

            similarity = max(0.0, min(1.0, 1.0 - dist))
            chunk_meta = ChunkMetadata.from_chroma_metadata(meta_dict)

            retrieved.append((chunk_meta, similarity))

        retrieved.sort(key=lambda item: item[1], reverse=True)
        return retrieved

    def retrieve_with_text(
        self,
        query: str,
        top_k: int = 4,
        course_code: Optional[str] = None,
        doc_type: Optional[str] = None,
        exclude_references: bool = True,
    ) -> List[Tuple[str, ChunkMetadata, float]]:
        """
        Retrieve chunks as (text, metadata, similarity_score) tuples.
        Used by the LLM generation stage.
        """
        try:
            results = self._query_collection(
                query,
                top_k,
                course_code,
                doc_type,
                exclude_references,
            )
        except Exception:
            logger.exception("Error executing Chroma query")
            return []

        retrieved = []

        if (
            not results
            or not results.get("documents")
            or not results["documents"][0]
        ):
            return retrieved

        documents = results["documents"][0]
        metadatas = (
            results["metadatas"][0]
            if results.get("metadatas")
            else []
        )
        distances = (
            results["distances"][0]
            if results.get("distances")
            else []
        )

        for i, chunk_text in enumerate(documents):
            meta_dict = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 1.0

            similarity = max(0.0, min(1.0, 1.0 - dist))
            chunk_meta = ChunkMetadata.from_chroma_metadata(meta_dict)

            retrieved.append((chunk_text, chunk_meta, similarity))

        retrieved.sort(key=lambda item: item[2], reverse=True)
        return retrieved

    def retrieve_for_topics(
        self,
        topics: List[str],
        top_k: int = 4,
        course_code: Optional[str] = None,
        doc_type: Optional[str] = None,
        exclude_references: bool = True,
    ) -> List[Tuple[str, ChunkMetadata, float]]:
        """
        Search each topic independently, then merge and deduplicate
        the retrieved chunks.

        Each topic gets its own top_k retrieval allowance.
        """
        merged = []
        seen_chunks = set()

        for topic in topics:
            topic = topic.strip()

            if not topic:
                continue

            topic_results = self.retrieve_with_text(
                query=topic,
                top_k=top_k,
                course_code=course_code,
                doc_type=doc_type,
                exclude_references=exclude_references,
            )

            logger.info(
                "Retrieved %d chunks for topic: %s",
                len(topic_results),
                topic[:100],
            )

            for chunk_text, metadata, score in topic_results:
                key = self._chunk_key(chunk_text, metadata)

                if key in seen_chunks:
                    continue

                seen_chunks.add(key)
                merged.append((chunk_text, metadata, score))

        merged.sort(key=lambda item: item[2], reverse=True)
        return merged

    def evaluate_relevance(
        self,
        retrieved: List[Tuple[ChunkMetadata, float]],
        threshold: Optional[float] = None,
    ) -> Tuple[bool, float]:
        """Return (is_relevant, confidence_score)."""
        thresh = (
            threshold
            if threshold is not None
            else self.relevance_threshold
        )

        if not retrieved:
            return False, 0.0

        top_similarity = retrieved[0][1]
        return top_similarity >= thresh, top_similarity

    def get_citations(
        self,
        retrieved: List[Tuple[ChunkMetadata, float]],
    ) -> List[Citation]:
        """Build deduplicated citations from stored metadata."""
        citations = []
        seen = set()

        for chunk_meta, _ in retrieved:
            key = (
                chunk_meta.doc_title,
                chunk_meta.page_number,
                chunk_meta.section,
            )

            if key in seen:
                continue

            seen.add(key)

            citations.append(
                Citation(
                    doc_title=chunk_meta.doc_title,
                    section=chunk_meta.section,
                    page_number=chunk_meta.page_number,
                    source_path=chunk_meta.source_path,
                    chunk_id=chunk_meta.chunk_id,
                )
            )

        return citations

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Day 6 retrieval workflow retained for backward compatibility.
        """
        retrieved = self.retrieve(
            query=request.query,
            top_k=request.top_k,
            course_code=request.course_code,
            doc_type=request.doc_type,
        )

        is_relevant, confidence = self.evaluate_relevance(retrieved)

        if not is_relevant:
            logger.info(
                "Query refused (confidence %.3f < threshold %.2f): %s",
                confidence,
                self.relevance_threshold,
                request.query[:50],
            )

            return QueryResponse(
                answer=REFUSAL_MESSAGE,
                citations=[],
                refused=True,
                confidence_score=round(confidence, 4),
            )

        citations = self.get_citations(retrieved)
        top_chunk = retrieved[0][0]

        answer_preview = (
            f"Based on {top_chunk.doc_title} "
            f"({top_chunk.section}, Page {top_chunk.page_number}): "
            f"Relevant evidence was retrieved across "
            f"{len(retrieved)} supporting chunk(s)."
        )

        return QueryResponse(
            answer=answer_preview,
            citations=citations,
            refused=False,
            confidence_score=round(confidence, 4),
        )