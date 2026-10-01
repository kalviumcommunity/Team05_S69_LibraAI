"""
LibraAI - Day 10 UI, Demo & Viva Verification Test Suite
Tests for Day 10 deliverables:
- Frontend benchmark query presets and execution helper
- Live viva demonstration runner (demo.py)
- Course code and document type filter support (FR-22)
- Viva presentation guide completeness
Reference: PRD §8.1, §8.5, FR-01, FR-02, FR-17, FR-22, NFR-01
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.app import VIVA_BENCHMARK_QUERIES, execute_query, check_backend_health
from demo import DEMO_SCENARIOS, run_demo
from config.corpus_catalog import CORPUS_CATALOG


class TestFrontendBenchmarkPresets:

    def test_preset_queries_count(self):
        """All 13 ground-truth benchmark cases must be present in the UI presets."""
        assert len(VIVA_BENCHMARK_QUERIES) == 13

    def test_preset_queries_format_and_ids(self):
        """Each preset must contain valid id, label, category, and query string."""
        expected_ids = [f"GT-{i:02d}" for i in range(1, 14)]
        actual_ids = [q["id"] for q in VIVA_BENCHMARK_QUERIES]
        assert actual_ids == expected_ids

        for q in VIVA_BENCHMARK_QUERIES:
            assert len(q["query"]) > 15
            assert len(q["label"]) > 5
            assert "category" in q

    def test_preset_queries_refusal_distribution(self):
        """Must have exactly 10 in-corpus and 3 refusal test cases."""
        in_corpus = [q for q in VIVA_BENCHMARK_QUERIES if "Refusal" not in q["category"]]
        out_corpus = [q for q in VIVA_BENCHMARK_QUERIES if "Refusal" in q["category"]]
        assert len(in_corpus) == 10
        assert len(out_corpus) == 3


class TestFrontendExecutionHelper:

    def test_execute_query_in_corpus(self):
        """In-corpus query executed through frontend helper must return grounded response."""
        res = execute_query(
            question="What percentage of participants in the password reuse study reused some password verbatim?",
            top_k=3,
        )
        assert res["refused"] is False
        assert len(res["citations"]) >= 1
        assert res["confidence_score"] >= 0.35
        assert res["latency"] >= 0.0
        assert "engine" in res

    def test_execute_query_out_of_corpus_refused(self):
        """Out-of-corpus query must return safe refusal with 0 citations."""
        res = execute_query(
            question="On what exact date did Parisian revolutionaries storm the Bastille fortress?",
            top_k=3,
        )
        assert res["refused"] is True
        assert res["citations"] == []
        assert res["confidence_score"] < 0.35
        assert res["latency"] >= 0.0

    def test_execute_query_with_course_filter(self):
        """Filtering by course code must succeed and return valid response."""
        res = execute_query(
            question="How does AI augment university library research processes?",
            top_k=3,
            course_code="LIS-101",
        )
        assert isinstance(res, dict)
        assert "answer" in res

    def test_execute_query_with_doc_type_filter(self):
        """Filtering by doc type must succeed and return valid response."""
        res = execute_query(
            question="In the CPUlator ARM assembly program, what are final register values?",
            top_k=3,
            doc_type="course_material",
        )
        assert isinstance(res, dict)
        assert "answer" in res

    def test_check_backend_health_returns_dict(self):
        """Health check helper must return online boolean and data dict or None."""
        health = check_backend_health()
        assert isinstance(health, dict)
        assert "online" in health
        assert isinstance(health["online"], bool)


class TestVivaDemoRunner:

    def test_demo_scenarios_structure(self):
        """Demo runner must contain 3 core test scenarios."""
        assert len(DEMO_SCENARIOS) == 3
        for s in DEMO_SCENARIOS:
            assert "title" in s
            assert "query" in s
            assert "expected_refusal" in s
            assert "doc" in s

    def test_demo_scenarios_execution(self):
        """Running the full demo script must return exit code 0 (all pass)."""
        ret = run_demo()
        assert ret == 0


class TestVivaDocumentationCompleteness:

    def test_viva_preparation_doc_exists(self):
        """VIVA_PREPARATION.md must exist in root repository."""
        doc_path = os.path.join(os.path.dirname(__file__), "..", "VIVA_PREPARATION.md")
        assert os.path.exists(doc_path)

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Executive Summary" in content
        assert "End-to-End System Architecture" in content
        assert "Technical Decisions & Defense" in content
        assert "Live Viva Demonstration Script" in content
        assert "Benchmark Evaluation Scorecard" in content
