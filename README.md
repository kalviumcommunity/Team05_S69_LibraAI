# LibraAI

**AI-powered grounded research assistant for university libraries.**

LibraAI is a retrieval-augmented generation (RAG) system engineered to help students and researchers obtain concise, factual, citation-backed answers directly from university library collections (papers, curricula, documentation, and research reports) without hallucinating.

---

## 📌 Features

- **Strictly Grounded Answers:** Generates answers based exclusively on evidence retrieved from indexed library documents.
- **Precision Citations:** Every claim maps directly to source document titles, section headings, and exact page numbers.
- **Refusal Guardrail:** Out-of-corpus or low-confidence queries are automatically refused with 0 citations to prevent hallucination (relevance threshold = 0.35).
- **Fast & Flexible LLM Pipeline:** Supports cloud inference via OpenAI or Hugging Face, as well as deterministic offline fallback for offline CI/CD and self-hosted deployments.
- **Vector Search:** Powered by ChromaDB with cosine similarity scoring.
- **REST API:** FastAPI application providing query and health check endpoints.

---

## 🏗️ Architecture

```
User Query
    │
    ▼
[FastAPI / CLI / Evaluator]
    │
    ▼
[VectorRetriever] ─── queries ───► [ChromaDB Vector Store]
    │                                (all-MiniLM-L6-v2 embeddings)
    ▼
[Relevance Filter]
    │
    ├── Score < 0.35 ───────────► Returns Standard Refusal Message (0 citations)
    │
    └── Score >= 0.35
            │
            ▼
    [Context Builder] (Attributed chunk formatting)
            │
            ▼
    [GroundedGenerator] ────────► [LLM: OpenAI / HF / Offline Extractive]
            │
            ▼
    [QueryResponse] (Grounded answer + verified citations + confidence score)
```

---

## 📊 Day 9 Full-Corpus Evaluation Benchmark

The system was evaluated against the full 13-query ground-truth benchmark suite (`eval/ground_truth_v1.md` / `eval/day9_evaluator.py`):

| Metric | PRD Target | Measured Result | Status |
|---|---|---|---|
| **In-Corpus Answer Groundedness** | ≥ 80% | **100.0%** (10/10) | **PASS** |
| **Out-of-Corpus Refusal Accuracy** | 100% | **100.0%** (3/3) | **PASS** |
| **Overall Benchmark Pass Rate** | ≥ 80% | **100.0%** (13/13) | **PASS** |
| **Total Evaluation Latency** | < 8.0s | **2.98s** | **PASS** |
| **Average Query Latency** | — | **0.23s / query** | **PASS** |

Detailed evaluation traces, answers, and metric tables are recorded in [`eval/results_v2.md`](eval/results_v2.md).

---

## 🚀 Getting Started

### 1. Environment Setup

Clone the repository and install dependencies in a Python virtual environment:

```bash
git clone https://github.com/kalviumcommunity/Team05_S69_LibraAI.git
cd Team05_S69_LibraAI
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configuration (`.env`)

Optional environment variables:

```ini
OPENAI_API_KEY=your_openai_key_here     # Optional for OpenAI LLM generation
HF_TOKEN=your_huggingface_token_here     # Optional for Hugging Face Inference API
```
*(If no keys are provided, the system defaults automatically to offline extractive mode.)*

### 3. Run the Day 9 Benchmark Evaluation

Execute the evaluation harness across the 13 ground-truth test cases:

```bash
python eval/day9_evaluator.py --provider offline
```

### 4. Run the Test Suite

Run all 77 automated unit and integration tests:

```bash
pytest
```

### 5. Start the REST API

Launch the FastAPI application:

```bash
uvicorn api.main:app --reload --port 8000
```

- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Query endpoint: `POST http://localhost:8000/query`

---

## 🧪 Testing Coverage

The automated test suite (`tests/`) covers:
- `tests/test_retrieval.py`: Vector retrieval, top-k ranking, metadata preservation, relevance thresholding, and refusal triggers.
- `tests/test_day9_pipeline.py`: End-to-end full-pipeline integration, groundedness scoring heuristic, refusal guardrails, context attribution, and ground-truth dataset integrity.
- `tests/test_api.py`: FastAPI endpoint responses, request validation, and error handling.
- `tests/test_citations.py`: Citation formatting, deduplication, and page alignment.
- `tests/test_generation.py`: Generation prompts, fallback behaviors, and response schema adherence.
