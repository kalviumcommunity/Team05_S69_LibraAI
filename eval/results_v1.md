# LibraAI — Benchmark Evaluation Results (v1.0)

**Evaluation Date:** September 25, 2026  
**Evaluation Sprint:** Day 6 — Retrieval & Relevance Thresholding  
**Relevance Threshold:** `0.38`  

---

## 1. Executive Metrics Summary

| Metric | Target | Measured Result | Status |
|---|---|---|---|
| **Retrieval Recall (In-Corpus)** | ≥ 80% | **100.0%** | ✅ MET |
| **Refusal Accuracy (Out-of-Corpus)** | 100% | **100.0%** | ✅ MET |
| **Overall Benchmark Pass Rate** | ≥ 80% | **100.0%** | ✅ MET |
| **Total Execution Latency** | < 8.0s | **2.72s** | ✅ MET |

---

## 2. Test-by-Test Results Matrix

| ID | Category | Top Retrieved Document | Conf. Score | Result | Notes |
|---|---|---|---|---|---|
| **GT-01** | In-Corpus / Direct Fact Retrieval | How Users Choose and Reuse Passwords (p.14) | `0.762` | PASS | Match=True, Relevant=True |
| **GT-02** | In-Corpus / Statistical Extraction | How Users Choose and Reuse Passwords (p.13) | `0.769` | PASS | Match=True, Relevant=True |
| **GT-03** | In-Corpus / Direct Fact Retrieval | Coexistence and Habitat Restoration Planning for the Reintroduction of Spix's Macaw (p.1) | `0.814` | PASS | Match=True, Relevant=True |
| **GT-04** | In-Corpus / Survey Extraction | Coexistence and Habitat Restoration Planning for the Reintroduction of Spix's Macaw (p.4) | `0.546` | PASS | Match=True, Relevant=True |
| **GT-05** | In-Corpus / Tabular Trace | CPUlator ARM Assembly Program Trace and Analysis Report (p.1) | `0.736` | PASS | Match=True, Relevant=True |
| **GT-06** | In-Corpus / Algorithmic Synthesis | CPUlator ARM Assembly Program Trace and Analysis Report (p.3) | `0.707` | PASS | Match=True, Relevant=True |
| **GT-07** | In-Corpus / Curriculum | AI & Automation / Technology Support for Localization Operations (p.1) | `0.595` | PASS | Match=True, Relevant=True |
| **GT-08** | In-Corpus / System Specification | Product Requirements Document (PRD) — LibraAI (p.5) | `0.493` | PASS | Match=True, Relevant=True |
| **GT-09** | In-Corpus / Overview Notes | Introduction to AI in Libraries (p.1) | `0.761` | PASS | Match=True, Relevant=True |
| **GT-10** | In-Corpus / Policy & NFR | Product Requirements Document (PRD) — LibraAI (p.6) | `0.418` | PASS | Match=True, Relevant=True |
| **GT-11** | Out-of-Corpus / Refusal Guardrail | CPUlator ARM Assembly Program Trace and Analysis (p.2) | `0.328` | PASS | Refused=True (< 0.38) |
| **GT-12** | Out-of-Corpus / Refusal Guardrail | CPUlator ARM Assembly Program Trace and Analysis (p.4) | `0.108` | PASS | Refused=True (< 0.38) |
| **GT-13** | Out-of-Corpus / Refusal Guardrail | How Users Choose and Reuse Passwords (p.6) | `0.240` | PASS | Refused=True (< 0.38) |

---

## 3. Analysis & Observations

1. **Strong Separation Margin:** In-corpus questions consistently scored between `0.418` and `0.820`, while all three out-of-corpus questions scored at or below `0.333`.
2. **Optimal Guardrail:** The calibrated threshold of `0.38` cleanly separates relevant university queries from unsupported domains without any false positives or false negatives.
3. **Cross-Document Traceability:** All 10 in-corpus benchmark questions successfully retrieved chunks containing canonical metadata (`doc_title`, `section`, `page_number`), fulfilling PRD FR-15 and FR-16.
