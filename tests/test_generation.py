"""
LibraAI — Day 8 End-to-End Generation Test
Tests the GroundedGenerator pipeline with ground-truth questions.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.schema import QueryRequest
from generation.generator import GroundedGenerator


def run_test(generator, question, expected_behavior):
    print(f"\n{'='*60}")
    print(f"Q: {question}")
    print(f"Expected: {expected_behavior}")
    print("-" * 60)

    request = QueryRequest(query=question, top_k=4)
    response = generator.query(request)

    print(f"Refused: {response.refused}")
    print(f"Confidence: {response.confidence_score}")
    print(f"Answer: {response.answer[:500]}")
    if response.citations:
        print(f"Citations ({len(response.citations)}):")
        for c in response.citations:
            print(f"  - {c.doc_title}, Page {c.page_number} ({c.section})")
    print("=" * 60)


def main():
    print("Initializing GroundedGenerator (offline mode)...")
    generator = GroundedGenerator(provider="offline")

    # GT-01: In-corpus direct fact
    run_test(
        generator,
        "What percentage of participants in the password reuse study reused some password verbatim?",
        "In-corpus: Should return answer from doc01, Page 14"
    )

    # GT-03: In-corpus direct fact
    run_test(
        generator,
        "In what year was the Spix's macaw declared extinct in the wild?",
        "In-corpus: Should return answer from doc02, Page 1-2"
    )

    # GT-08: In-corpus specification
    run_test(
        generator,
        "What is the maximum end-to-end query latency target for LibraAI?",
        "In-corpus: Should return answer from doc07, Section 7.1"
    )

    # GT-11: Out-of-corpus refusal
    run_test(
        generator,
        "How does Shor's algorithm achieve polynomial-time integer factorization?",
        "Out-of-corpus: Should REFUSE with 'I don't know'"
    )

    # GT-12: Out-of-corpus refusal
    run_test(
        generator,
        "On what date did Parisian revolutionaries storm the Bastille fortress?",
        "Out-of-corpus: Should REFUSE with 'I don't know'"
    )


if __name__ == "__main__":
    main()
