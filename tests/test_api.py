"""
Unit & Contract Tests for Day 2 Deliverables:
1. Metadata Schema serialization & roundtrip.
2. FastAPI Health endpoint.
3. FastAPI Query contract (in-corpus & refusal paths).
Reference: PRD Appendix B, FR-05, FR-10, FR-19
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from config.schema import ChunkMetadata, QueryRequest, QueryResponse

client = TestClient(app)


def test_metadata_schema_chroma_roundtrip():
    """Verify ChunkMetadata safely converts to and from ChromaDB primitive dictionary."""
    meta = ChunkMetadata(
        chunk_id="doc01_p14_c002",
        doc_title="How Users Choose and Reuse Passwords",
        doc_type="research_paper",
        author="Bonneau et al.",
        course_code="CS-SEC",
        section="V. Password Extraction",
        page_number=14,
        source_path="data/doc01_password_reuse_research_paper.pdf",
        is_reference=False,
        token_count=350,
    )
    chroma_dict = meta.to_chroma_metadata()

    # Chroma only accepts primitive types
    for key, val in chroma_dict.items():
        assert isinstance(val, (int, float, str, bool)), f"Non-primitive field {key}: {type(val)}"

    reconstructed = ChunkMetadata.from_chroma_metadata(chroma_dict)
    assert reconstructed.chunk_id == meta.chunk_id
    assert reconstructed.doc_title == meta.doc_title
    assert reconstructed.page_number == meta.page_number
    assert reconstructed.course_code == meta.course_code
    assert reconstructed.is_reference is False


def test_health_check_endpoint():
    """Verify GET /health returns 200 OK and valid status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_query_in_corpus_contract():
    """Verify POST /query returns a properly structured QueryResponse with citation for in-corpus question."""
    payload = {
        "query": "What percentage of participants reused passwords verbatim?",
        "top_k": 4,
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Validate against QueryResponse model
    parsed = QueryResponse(**data)
    assert parsed.refused is False
    assert len(parsed.answer) > 20
    assert len(parsed.citations) >= 1

    citation = parsed.citations[0]
    assert citation.doc_title == "How Users Choose and Reuse Passwords"
    assert citation.page_number >= 1  # real retriever returns actual page
    assert len(citation.section) > 0   # section populated from real chunk metadata
    assert citation.source_path.endswith(".pdf")


def test_query_refusal_contract():
    """Verify POST /query triggers the refusal path on an out-of-corpus question."""
    payload = {
        "query": "How does Shor's quantum factoring algorithm work?",
        "top_k": 4,
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    parsed = QueryResponse(**data)
    assert parsed.refused is True
    assert "I don't know" in parsed.answer or "not covered" in parsed.answer
    assert len(parsed.citations) == 0


def test_query_validation_error():
    """Verify invalid input payload (e.g. empty query) triggers 422 Unprocessable Entity."""
    payload = {
        "query": "",  # min_length is 2
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 422


if __name__ == "__main__":
    print("Running tests manually...")
    test_metadata_schema_chroma_roundtrip()
    print("✅ test_metadata_schema_chroma_roundtrip passed")
    test_health_check_endpoint()
    print("✅ test_health_check_endpoint passed")
    test_query_in_corpus_contract()
    print("✅ test_query_in_corpus_contract passed")
    test_query_refusal_contract()
    print("✅ test_query_refusal_contract passed")
    test_query_validation_error()
    print("✅ test_query_validation_error passed")
    print("\nALL TESTS PASSED SUCCESSFULLY! 🚀")
