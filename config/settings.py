"""
LibraAI - Centralized Settings Module
Day 10 Deliverable: Single source of truth for all configuration values.
Reference: PRD §6, §7, §8, NFR-03
"""

import os
from pathlib import Path

# ─── Repository root ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.resolve()

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR              = REPO_ROOT / "data"
CHROMA_DIR            = DATA_DIR / "chroma_db"
CHUNKS_DIR            = DATA_DIR / "chunks"
CLEANED_DIR           = DATA_DIR / "cleaned"
PROCESSED_DIR         = DATA_DIR / "processed"
EVAL_DIR              = REPO_ROOT / "eval"
INGESTION_ERROR_LOG   = REPO_ROOT / "ingestion_errors.log"
CHUNKING_ERROR_LOG    = REPO_ROOT / "chunking_errors.log"
EMBEDDING_ERROR_LOG   = REPO_ROOT / "embedding_errors.log"

# ─── ChromaDB collection ──────────────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "libra_ai_corpus"
CHROMA_DISTANCE_SPACE  = "cosine"

# ─── Embedding model ──────────────────────────────────────────────────────────
# Primary: OpenAI text-embedding-3-small (if OPENAI_API_KEY present)
# Fallback: ChromaDB local all-MiniLM-L6-v2 (ONNX)
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"

# ─── LLM / Generation ─────────────────────────────────────────────────────────
NVIDIA_DEFAULT_MODEL   = "meta/llama-3.3-70b-instruct"
NVIDIA_API_BASE        = "https://integrate.api.nvidia.com/v1"
LLM_TEMPERATURE        = 0.2
LLM_MAX_TOKENS         = 1024
LLM_TIMEOUT_SECONDS    = 60
LLM_MAX_RETRIES        = 2

# ─── Retrieval ────────────────────────────────────────────────────────────────
# Calibrated threshold: in-corpus scores ≥ 0.41, out-of-corpus ≤ 0.33
DEFAULT_RELEVANCE_THRESHOLD = 0.35
DEFAULT_TOP_K               = 4
MAX_TOP_K                   = 20

# ─── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE              = 400    # target tokens per chunk
CHUNK_OVERLAP           = 60     # ~15% overlap
CHUNK_ENCODING          = "cl100k_base"
CHUNK_SEPARATORS        = ["\n\n## ", "\n\n### ", "\n\n", "\n", " ", ""]

# ─── Indexing pipeline ────────────────────────────────────────────────────────
INDEX_BATCH_SIZE        = 50

# ─── API / Backend ────────────────────────────────────────────────────────────
BACKEND_HOST            = "0.0.0.0"
BACKEND_PORT            = 8000
FRONTEND_PORT           = 8501
API_BASE_URL            = f"http://localhost:{BACKEND_PORT}"
QUERY_ENDPOINT          = f"{API_BASE_URL}/query"
HEALTH_ENDPOINT         = f"{API_BASE_URL}/health"

# ─── Performance targets (PRD §7.1) ──────────────────────────────────────────
LATENCY_TARGET_SECONDS     = 10.0   # max end-to-end p95 latency
RECALL_TARGET_PCT          = 80.0   # min in-corpus retrieval recall
GROUNDEDNESS_TARGET_PCT    = 80.0   # min answer groundedness
REFUSAL_ACCURACY_TARGET    = 100.0  # required OOC refusal rate
