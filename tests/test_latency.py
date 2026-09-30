"""
LibraAI — End-to-End Latency Test Harness
Day 10 Deliverable: Measures query response time on 5 representative questions.
Reference: PRD §7.1 — end-to-end latency target < 8–10 seconds.
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import LATENCY_TARGET_SECONDS
from config.schema import QueryRequest
from generation.generator import GroundedGenerator

# 5 representative questions covering all major corpus documents
LATENCY_QUESTIONS = [
    {
        "id": "LT-01",
        "question": "What percentage of participants reused some password verbatim?",
        "expected": "in-corpus",
    },
    {
        "id": "LT-02",
        "question": "In what year was the Spix's macaw declared extinct in the wild?",
        "expected": "in-corpus",
    },
    {
        "id": "LT-03",
        "question": "What are the final decimal values of registers r6 and r7?",
        "expected": "in-corpus",
    },
    {
        "id": "LT-04",
        "question": "What is the maximum end-to-end query latency target for LibraAI?",
        "expected": "in-corpus",
    },
    {
        "id": "LT-05",
        "question": "How does Shor's algorithm achieve polynomial-time factorization?",
        "expected": "out-of-corpus (refusal)",
    },
]


def run_latency_test():
    print("=" * 70)
    print("LibraAI — End-to-End Latency Measurement (offline/extractive mode)")
    print(f"Target: < {LATENCY_TARGET_SECONDS:.0f}s per query")
    print("=" * 70)

    generator = GroundedGenerator(provider="offline")

    results = []
    total_time = 0.0

    for tc in LATENCY_QUESTIONS:
        request = QueryRequest(query=tc["question"], top_k=4)

        start = time.perf_counter()
        response = generator.query(request)
        elapsed = time.perf_counter() - start

        total_time += elapsed
        within_target = elapsed <= LATENCY_TARGET_SECONDS
        status = "PASS" if within_target else "SLOW"

        print(f"\n[{status}] {tc['id']}: {tc['question'][:60]}...")
        print(f"  Latency:    {elapsed:.3f}s  (target < {LATENCY_TARGET_SECONDS}s)")
        print(f"  Refused:    {response.refused}")
        print(f"  Confidence: {response.confidence_score}")
        print(f"  Expected:   {tc['expected']}")

        results.append({
            "id": tc["id"],
            "question": tc["question"],
            "latency_s": round(elapsed, 3),
            "within_target": within_target,
            "refused": response.refused,
            "confidence": response.confidence_score,
            "expected": tc["expected"],
            "status": status,
        })

    avg_latency = total_time / len(LATENCY_QUESTIONS)
    passed = sum(1 for r in results if r["within_target"])
    outliers = [r for r in results if not r["within_target"]]

    print("\n" + "=" * 70)
    print("LATENCY SUMMARY")
    print("=" * 70)
    print(f"Questions tested:  {len(LATENCY_QUESTIONS)}")
    print(f"Within target:     {passed}/{len(LATENCY_QUESTIONS)}")
    print(f"Average latency:   {avg_latency:.3f}s")
    print(f"Total wall time:   {total_time:.3f}s")

    if outliers:
        print(f"\nOutliers (> {LATENCY_TARGET_SECONDS}s):")
        for o in outliers:
            print(f"  {o['id']}: {o['latency_s']:.3f}s  — {o['question'][:55]}...")
    else:
        print(f"\nAll queries completed within the {LATENCY_TARGET_SECONDS}s target.")

    # Write results to eval/
    result_path = os.path.join(
        os.path.dirname(__file__), "..", "eval", "latency_results_v1.json"
    )
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "target_seconds": LATENCY_TARGET_SECONDS,
                "avg_latency_s": round(avg_latency, 3),
                "pass_rate": f"{passed}/{len(LATENCY_QUESTIONS)}",
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nLatency results saved to: {os.path.abspath(result_path)}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run_latency_test()
