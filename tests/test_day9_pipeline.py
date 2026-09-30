"""
LibraAI - Day 9 Full-Pipeline Pytest Test Suite
Tests the complete RAG pipeline end-to-end in offline (no API key) mode.
Reference: PRD 7.1, 7.2, FR-05, FR-08-FR-13, NFR-03
"""

import os
import sys
import time
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.schema import QueryRequest, QueryResponse
from generation.generator import GroundedGenerator, generate_answer, _generate_offline_fallback, _format_context
from retrieval.retriever import VectorRetriever, REFUSAL_MESSAGE
from eval.day9_evaluator import evaluate_groundedness, GROUND_TRUTH_CASES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def offline_generator():
    """Shared GroundedGenerator in offline mode for the full test module."""
    return GroundedGenerator(provider="offline")


@pytest.fixture(scope="module")
def retriever():
    """Shared VectorRetriever for retrieval-level tests."""
    return VectorRetriever()


# ---------------------------------------------------------------------------
# 1. Groundedness heuristic unit tests
# ---------------------------------------------------------------------------

class TestGroundednessHeuristic:

    def test_out_of_corpus_refused_passes(self):
        assert evaluate_groundedness("I don't know", [], True, True) is True

    def test_out_of_corpus_not_refused_fails(self):
        assert evaluate_groundedness("The answer is 42", [], False, True) is False

    def test_in_corpus_keyword_match_passes(self):
        assert evaluate_groundedness("The memorability was cited by 34 participants", ["34", "memorability"], False, False) is True

    def test_in_corpus_no_keyword_match_fails(self):
        assert evaluate_groundedness("Something unrelated entirely", ["34", "memorability"], False, False) is False

    def test_in_corpus_refused_always_fails(self):
        assert evaluate_groundedness(REFUSAL_MESSAGE, ["keyword"], True, False) is False

    def test_in_corpus_no_keywords_non_empty_passes(self):
        assert evaluate_groundedness("Some answer text here", [], False, False) is True

    def test_in_corpus_no_keywords_empty_fails(self):
        assert evaluate_groundedness("", [], False, False) is False

    def test_case_insensitive_keyword_matching(self):
        assert evaluate_groundedness("Memorability was the key factor", ["memorability"], False, False) is True


# ---------------------------------------------------------------------------
# 2. Ground truth dataset integrity tests
# ---------------------------------------------------------------------------

class TestGroundTruthDataset:

    def test_has_13_cases(self):
        assert len(GROUND_TRUTH_CASES) == 13

    def test_has_10_in_corpus_cases(self):
        in_c = [c for c in GROUND_TRUTH_CASES if not c["is_out_of_corpus"]]
        assert len(in_c) == 10

    def test_has_3_out_of_corpus_cases(self):
        out_c = [c for c in GROUND_TRUTH_CASES if c["is_out_of_corpus"]]
        assert len(out_c) == 3

    def test_all_cases_have_id_and_question(self):
        for case in GROUND_TRUTH_CASES:
            assert "id" in case
            assert "question" in case
            assert len(case["question"]) > 10

    def test_out_of_corpus_cases_have_empty_keywords(self):
        out_c = [c for c in GROUND_TRUTH_CASES if c["is_out_of_corpus"]]
        for case in out_c:
            assert case["keywords"] == []

    def test_in_corpus_cases_have_target_doc(self):
        in_c = [c for c in GROUND_TRUTH_CASES if not c["is_out_of_corpus"]]
        for case in in_c:
            assert case["target_doc"] is not None


# ---------------------------------------------------------------------------
# 3. Context builder unit tests
# ---------------------------------------------------------------------------

class TestContextBuilder:

    def _make_meta(self, title="Test Doc", page=1, section="Intro"):
        from config.schema import ChunkMetadata
        return ChunkMetadata(
            chunk_id="test_p1_c0",
            doc_title=title,
            doc_type="notes",
            author="Test Author",
            section=section,
            page_number=page,
            source_path="data/test.pdf",
        )

    def test_context_includes_document_title(self):
        meta = self._make_meta(title="Password Study")
        context = _format_context([(meta, 0.75)], ["Chunk text here"])
        assert "Password Study" in context

    def test_context_includes_page_number(self):
        meta = self._make_meta(page=7)
        context = _format_context([(meta, 0.75)], ["Text"])
        assert "7" in context

    def test_context_includes_chunk_text(self):
        meta = self._make_meta()
        context = _format_context([(meta, 0.75)], ["The actual content here"])
        assert "The actual content here" in context

    def test_context_labels_multiple_chunks(self):
        meta = self._make_meta()
        context = _format_context([(meta, 0.8), (meta, 0.6)], ["First chunk", "Second chunk"])
        assert "Chunk 1" in context
        assert "Chunk 2" in context

    def test_empty_retrieved_gives_empty_context(self):
        context = _format_context([], [])
        assert context == ""


# ---------------------------------------------------------------------------
# 4. Offline fallback generation tests
# ---------------------------------------------------------------------------

class TestOfflineFallback:

    def _make_retrieved(self, title="Doc", page=1, section="S"):
        from config.schema import ChunkMetadata
        meta = ChunkMetadata(
            chunk_id="c1",
            doc_title=title,
            doc_type="notes",
            author="A",
            section=section,
            page_number=page,
            source_path="data/test.pdf",
        )
        return [(meta, 0.75)]

    def test_empty_retrieval_returns_refusal(self):
        result = _generate_offline_fallback([], [], "any question")
        assert result == REFUSAL_MESSAGE

    def test_non_empty_retrieval_returns_string(self):
        retrieved = self._make_retrieved()
        result = _generate_offline_fallback(retrieved, ["Some text content"], "question?")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_answer_contains_source_doc_title(self):
        retrieved = self._make_retrieved(title="Password Research")
        result = _generate_offline_fallback(retrieved, ["Content"], "question?")
        assert "Password Research" in result

    def test_answer_includes_page_number(self):
        retrieved = self._make_retrieved(page=14)
        result = _generate_offline_fallback(retrieved, ["Content"], "question?")
        assert "14" in result


# ---------------------------------------------------------------------------
# 5. GroundedGenerator pipeline tests (offline)
# ---------------------------------------------------------------------------

class TestGroundedGeneratorOffline:

    def test_in_corpus_query_returns_response(self, offline_generator):
        req = QueryRequest(query="What are the password reuse findings?", top_k=3)
        resp = offline_generator.query(req)
        assert isinstance(resp, QueryResponse)

    def test_in_corpus_query_not_refused(self, offline_generator):
        req = QueryRequest(query="What are the password reuse findings?", top_k=3)
        resp = offline_generator.query(req)
        assert resp.refused is False

    def test_in_corpus_query_returns_non_empty_answer(self, offline_generator):
        req = QueryRequest(query="What are the password reuse findings?", top_k=3)
        resp = offline_generator.query(req)
        assert resp.answer.strip() != ""

    def test_in_corpus_query_returns_citations(self, offline_generator):
        req = QueryRequest(query="What are the password reuse findings?", top_k=3)
        resp = offline_generator.query(req)
        assert isinstance(resp.citations, list)
        assert len(resp.citations) > 0

    def test_out_of_corpus_query_is_refused(self, offline_generator):
        req = QueryRequest(query="How does Shor algorithm factor integers on quantum computers?", top_k=3)
        resp = offline_generator.query(req)
        assert resp.refused is True

    def test_out_of_corpus_answer_is_refusal_message(self, offline_generator):
        req = QueryRequest(query="How does Shor algorithm factor integers on quantum computers?", top_k=3)
        resp = offline_generator.query(req)
        assert "don" in resp.answer.lower() or "not covered" in resp.answer.lower()

    def test_out_of_corpus_returns_empty_citations(self, offline_generator):
        req = QueryRequest(query="How does Shor algorithm factor integers on quantum computers?", top_k=3)
        resp = offline_generator.query(req)
        assert resp.citations == []

    def test_confidence_score_is_float(self, offline_generator):
        req = QueryRequest(query="What are the password reuse findings?", top_k=3)
        resp = offline_generator.query(req)
        assert isinstance(resp.confidence_score, float)

    def test_confidence_score_in_valid_range(self, offline_generator):
        req = QueryRequest(query="What are the password reuse findings?", top_k=3)
        resp = offline_generator.query(req)
        assert 0.0 <= resp.confidence_score <= 1.0

    def test_query_completes_under_10_seconds(self, offline_generator):
        req = QueryRequest(query="What is the LibraAI latency target?", top_k=3)
        t0 = time.perf_counter()
        offline_generator.query(req)
        latency = time.perf_counter() - t0
        assert latency < 10.0


# ---------------------------------------------------------------------------
# 6. Refusal guardrail integration tests (3 out-of-corpus GT cases)
# ---------------------------------------------------------------------------

class TestRefusalGuardrail:

    REFUSAL_QUERIES = [
        "How does Shor algorithm achieve polynomial-time integer factorization on a fault-tolerant quantum computer?",
        "On what exact date did Parisian revolutionaries storm the Bastille fortress during the French Revolution?",
        "What is the exact nucleotide sequence of the protospacer adjacent motif required by Streptococcus pyogenes Cas9?",
    ]

    @pytest.mark.parametrize("question", REFUSAL_QUERIES)
    def test_out_of_corpus_refused(self, question, offline_generator):
        req = QueryRequest(query=question, top_k=4)
        resp = offline_generator.query(req)
        assert resp.refused is True, f"Expected refusal for: {question[:60]}"

    @pytest.mark.parametrize("question", REFUSAL_QUERIES)
    def test_out_of_corpus_empty_citations(self, question, offline_generator):
        req = QueryRequest(query=question, top_k=4)
        resp = offline_generator.query(req)
        assert resp.citations == []

    @pytest.mark.parametrize("question", REFUSAL_QUERIES)
    def test_out_of_corpus_low_confidence(self, question, offline_generator):
        req = QueryRequest(query=question, top_k=4)
        resp = offline_generator.query(req)
        assert resp.confidence_score < 0.35, f"Confidence too high for out-of-corpus: {resp.confidence_score:.3f}"
