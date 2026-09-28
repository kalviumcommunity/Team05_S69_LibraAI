"""
LibraAI - Day 6 Retrieval & Relevance Thresholding Unit Tests
Tests for VectorRetriever, relevance guardrail, and citation extraction.
Reference: PRD §8.2, §8.3, §8.5, FR-04, FR-05, FR-06, FR-07, FR-08, FR-09, FR-10
"""

import os
import sys
import pytest

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.schema import ChunkMetadata, Citation, QueryRequest
from retrieval.retriever import VectorRetriever, DEFAULT_RELEVANCE_THRESHOLD, REFUSAL_MESSAGE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def retriever():
    """Shared VectorRetriever instance — uses pre-built ChromaDB index."""
    return VectorRetriever()


# ---------------------------------------------------------------------------
# Threshold sanity
# ---------------------------------------------------------------------------

def test_default_relevance_threshold_value():
    """Calibrated threshold must be 0.38 per Day 6 design decision."""
    assert DEFAULT_RELEVANCE_THRESHOLD == 0.38


def test_refusal_message_format():
    """Refusal message must include 'I don't know' or 'not covered' (FR-10)."""
    assert "I don't know" in REFUSAL_MESSAGE or "not covered" in REFUSAL_MESSAGE


# ---------------------------------------------------------------------------
# Retrieval — in-corpus queries
# ---------------------------------------------------------------------------

def test_retrieve_returns_list(retriever):
    """retrieve() must always return a list (never None or raises)."""
    results = retriever.retrieve("password reuse memorability", top_k=4)
    assert isinstance(results, list)


def test_retrieve_top_k_limit(retriever):
    """retrieve() must return at most top_k results."""
    results = retriever.retrieve("Spix's macaw Curaçá", top_k=3)
    assert len(results) <= 3


def test_retrieve_returns_chunk_metadata_and_score(retriever):
    """Each element in retrieve() result is a (ChunkMetadata, float) tuple."""
    results = retriever.retrieve("ARM assembly register values", top_k=2)
    assert len(results) >= 1
    meta, score = results[0]
    assert isinstance(meta, ChunkMetadata)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_retrieve_sorted_descending_by_similarity(retriever):
    """Results must be sorted by similarity score descending (highest relevance first)."""
    results = retriever.retrieve("AI research assistant library university", top_k=5)
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True), "Results not sorted descending"


def test_in_corpus_password_query_passes_threshold(retriever):
    """GT-01: password reuse query must retrieve relevant chunks above threshold."""
    results = retriever.retrieve(
        "What percentage of participants reused passwords verbatim and why?", top_k=4
    )
    is_relevant, confidence = retriever.evaluate_relevance(results)
    assert is_relevant, f"Expected relevant, got confidence={confidence:.3f}"
    assert confidence >= DEFAULT_RELEVANCE_THRESHOLD


def test_in_corpus_spix_macaw_query_passes_threshold(retriever):
    """GT-03: Spix's macaw query must retrieve relevant chunks above threshold."""
    results = retriever.retrieve(
        "When was the Spix's macaw declared extinct in the wild?", top_k=4
    )
    is_relevant, confidence = retriever.evaluate_relevance(results)
    assert is_relevant, f"Expected relevant, got confidence={confidence:.3f}"


def test_in_corpus_arm_assembly_query_passes_threshold(retriever):
    """GT-05: CPUlator ARM trace query must retrieve relevant chunks."""
    results = retriever.retrieve(
        "What are the final values in registers r6 and r7 after ARM program execution?", top_k=4
    )
    is_relevant, confidence = retriever.evaluate_relevance(results)
    assert is_relevant, f"Expected relevant, got confidence={confidence:.3f}"


def test_in_corpus_prd_query_passes_threshold(retriever):
    """GT-08: PRD latency and metric specification query must retrieve relevant chunks."""
    results = retriever.retrieve(
        "What is the maximum target end-to-end query latency for a live demonstration, "
        "and what are the target thresholds for retrieval recall and answer groundedness?",
        top_k=4,
    )
    is_relevant, confidence = retriever.evaluate_relevance(results)
    assert is_relevant, f"Expected relevant, got confidence={confidence:.3f}"


# ---------------------------------------------------------------------------
# Retrieval — out-of-corpus guardrail
# ---------------------------------------------------------------------------

def test_out_of_corpus_shor_algorithm_is_refused(retriever):
    """GT-11: Shor's quantum algorithm is outside corpus — must fall below threshold."""
    results = retriever.retrieve(
        "How does Shor's algorithm achieve polynomial time integer factorization?", top_k=4
    )
    is_relevant, confidence = retriever.evaluate_relevance(results)
    assert not is_relevant, f"Expected refusal, but got relevant with confidence={confidence:.3f}"


def test_out_of_corpus_french_revolution_is_refused(retriever):
    """GT-12: French Revolution is outside corpus — must fall below threshold."""
    results = retriever.retrieve(
        "What were the political consequences of the Storming of the Bastille?", top_k=4
    )
    is_relevant, confidence = retriever.evaluate_relevance(results)
    assert not is_relevant, f"Expected refusal, but got relevant with confidence={confidence:.3f}"


def test_out_of_corpus_crispr_is_refused(retriever):
    """GT-13: CRISPR/Cas9 PAM sequence is outside corpus — must fall below threshold."""
    results = retriever.retrieve(
        "What is the PAM sequence required by Streptococcus pyogenes Cas9?", top_k=4
    )
    is_relevant, confidence = retriever.evaluate_relevance(results)
    assert not is_relevant, f"Expected refusal, but got relevant with confidence={confidence:.3f}"


# ---------------------------------------------------------------------------
# evaluate_relevance edge cases
# ---------------------------------------------------------------------------

def test_evaluate_relevance_empty_list(retriever):
    """Empty retrieve result must return (False, 0.0)."""
    is_relevant, confidence = retriever.evaluate_relevance([])
    assert not is_relevant
    assert confidence == 0.0


def test_evaluate_relevance_custom_threshold(retriever):
    """Custom threshold overrides default when passed explicitly."""
    # Build a fake result with similarity 0.50
    dummy_meta = ChunkMetadata(
        chunk_id="test_p1_c001",
        doc_title="Test Doc",
        doc_type="notes",
        author="Test Author",
        section="Introduction",
        page_number=1,
        source_path="data/test.pdf",
        is_reference=False,
        token_count=100,
    )
    fake_results = [(dummy_meta, 0.50)]
    # With threshold 0.60 → not relevant
    is_rel_high, _ = retriever.evaluate_relevance(fake_results, threshold=0.60)
    assert not is_rel_high
    # With threshold 0.30 → relevant
    is_rel_low, _ = retriever.evaluate_relevance(fake_results, threshold=0.30)
    assert is_rel_low


# ---------------------------------------------------------------------------
# get_citations
# ---------------------------------------------------------------------------

def test_get_citations_deduplication(retriever):
    """Duplicate (doc_title, page_number, section) tuples must produce one citation."""
    dummy_meta = ChunkMetadata(
        chunk_id="doc01_p14_c001",
        doc_title="How Users Choose and Reuse Passwords",
        doc_type="research_paper",
        author="Hanamsagar et al.",
        section="V. Password Extraction",
        page_number=14,
        source_path="data/doc01.pdf",
        is_reference=False,
        token_count=250,
    )
    # Same doc/page/section, different chunk_id
    duplicate_meta = ChunkMetadata(
        chunk_id="doc01_p14_c002",
        doc_title="How Users Choose and Reuse Passwords",
        doc_type="research_paper",
        author="Hanamsagar et al.",
        section="V. Password Extraction",
        page_number=14,
        source_path="data/doc01.pdf",
        is_reference=False,
        token_count=300,
    )
    citations = retriever.get_citations([(dummy_meta, 0.8), (duplicate_meta, 0.7)])
    assert len(citations) == 1
    assert citations[0].doc_title == "How Users Choose and Reuse Passwords"
    assert citations[0].page_number == 14


def test_get_citations_multiple_unique_sources(retriever):
    """Multiple unique sources must each generate a separate citation."""
    meta1 = ChunkMetadata(
        chunk_id="doc01_p14_c001",
        doc_title="Doc One",
        doc_type="research_paper",
        author="Author A",
        section="Section 1",
        page_number=14,
        source_path="data/doc01.pdf",
        is_reference=False,
        token_count=200,
    )
    meta2 = ChunkMetadata(
        chunk_id="doc02_p1_c001",
        doc_title="Doc Two",
        doc_type="notes",
        author="Author B",
        section="Introduction",
        page_number=1,
        source_path="data/doc02.pdf",
        is_reference=False,
        token_count=150,
    )
    citations = retriever.get_citations([(meta1, 0.8), (meta2, 0.6)])
    assert len(citations) == 2
    titles = {c.doc_title for c in citations}
    assert "Doc One" in titles
    assert "Doc Two" in titles


# ---------------------------------------------------------------------------
# End-to-end query() workflow
# ---------------------------------------------------------------------------

def test_query_in_corpus_returns_answer_and_citations(retriever):
    """In-corpus query must return refused=False with at least one citation."""
    request = QueryRequest(query="What percentage of participants reused passwords verbatim?")
    response = retriever.query(request)
    assert not response.refused
    assert len(response.citations) >= 1
    assert response.confidence_score is not None
    assert response.confidence_score >= DEFAULT_RELEVANCE_THRESHOLD


def test_query_out_of_corpus_triggers_refusal(retriever):
    """Out-of-corpus query must return refused=True with 0 citations."""
    request = QueryRequest(query="How does Shor's quantum algorithm factorize integers?")
    response = retriever.query(request)
    assert response.refused is True
    assert len(response.citations) == 0
    assert "I don't know" in response.answer or "not covered" in response.answer


def test_query_response_confidence_is_float_in_range(retriever):
    """confidence_score in QueryResponse must be a float in [0, 1]."""
    request = QueryRequest(query="Spix macaw reintroduction habitat Brazil")
    response = retriever.query(request)
    assert response.confidence_score is not None
    assert 0.0 <= response.confidence_score <= 1.0


# ---------------------------------------------------------------------------
# FastAPI integration — /query now uses real retriever
# ---------------------------------------------------------------------------

def test_api_query_endpoint_in_corpus():
    """POST /query with in-corpus question must return 200 with citations via real retriever."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    payload = {"query": "What percentage of participants reused passwords verbatim?"}
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["refused"] is False
    assert len(data["citations"]) >= 1
    assert data["confidence_score"] >= DEFAULT_RELEVANCE_THRESHOLD


def test_api_query_endpoint_out_of_corpus():
    """POST /query with out-of-corpus question must return refused=True via real retriever."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    payload = {"query": "How does the French Revolution relate to quantum computing?"}
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["refused"] is True
    assert data["citations"] == []


def test_api_health_version():
    """GET /health must return version 2.0.0 (Day 6 upgrade)."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["version"] == "2.0.0"
    assert resp.json()["stage"] == "Day 6 - Real Retrieval"
