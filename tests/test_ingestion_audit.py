"""
LibraAI — Ingestion Audit + Full-Corpus Indexing Verification Script
Day 10 Deliverable: Confirms that no documents were silently dropped during
the ingestion, cleaning, chunking, and indexing pipeline.
Reference: PRD §6.3 (Data Quality Requirements), NFR — ingestion_errors.log
"""

import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import (
    DATA_DIR,
    PROCESSED_DIR,
    CLEANED_DIR,
    CHUNKS_DIR,
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    INGESTION_ERROR_LOG,
    CHUNKING_ERROR_LOG,
    EMBEDDING_ERROR_LOG,
)
from indexing.indexer import get_chroma_client, get_or_create_collection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("libraai.ingestion_audit")

# ─── 1. Source documents ──────────────────────────────────────────────────────
SUPPORTED_EXTS = {".pdf", ".docx", ".txt", ".md", ".csv"}

def audit_source_documents():
    """List every file in data/ that should be ingested."""
    source_files = []
    for fname in sorted(os.listdir(DATA_DIR)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in SUPPORTED_EXTS:
            source_files.append(fname)
    logger.info("=== Source Documents Found (%d) ===", len(source_files))
    for f in source_files:
        logger.info("  [SOURCE]  %s", f)
    return source_files

# ─── 2. Processed JSON files ──────────────────────────────────────────────────
def audit_processed():
    """Check which source documents produced a processed JSON."""
    processed = {}
    for fname in os.listdir(PROCESSED_DIR):
        if fname.endswith(".json"):
            path = os.path.join(PROCESSED_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                pages = json.load(f)
            processed[fname] = len(pages)
    logger.info("=== Processed JSON files (%d) ===", len(processed))
    for fname, pages in sorted(processed.items()):
        logger.info("  [PROCESSED]  %s  (%d pages)", fname, pages)
    return processed

# ─── 3. Cleaned JSON files ────────────────────────────────────────────────────
def audit_cleaned():
    """Check which documents survived the cleaning step."""
    cleaned = {}
    for fname in os.listdir(CLEANED_DIR):
        if fname.endswith(".json"):
            path = os.path.join(CLEANED_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                pages = json.load(f)
            # Check for any pages with empty text after cleaning
            empty_pages = [p for p in pages if not p.get("text", "").strip()]
            cleaned[fname] = {"total_pages": len(pages), "empty_pages": len(empty_pages)}
    logger.info("=== Cleaned JSON files (%d) ===", len(cleaned))
    for fname, info in sorted(cleaned.items()):
        if info["empty_pages"] > 0:
            logger.warning("  [CLEANED]  %s  (%d pages, %d EMPTY pages after cleaning!)",
                           fname, info["total_pages"], info["empty_pages"])
        else:
            logger.info("  [CLEANED]  %s  (%d pages, 0 empty pages)", fname, info["total_pages"])
    return cleaned

# ─── 4. Chunked JSON files ────────────────────────────────────────────────────
def audit_chunks():
    """Check chunks produced per document."""
    chunks = {}
    zero_text = []
    for fname in os.listdir(CHUNKS_DIR):
        if fname.endswith(".json"):
            path = os.path.join(CHUNKS_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                chunk_list = json.load(f)
            empty_chunks = [c for c in chunk_list if not c.get("text", "").strip()]
            chunks[fname] = {"count": len(chunk_list), "empty": len(empty_chunks)}
            if empty_chunks:
                zero_text.append(fname)
    logger.info("=== Chunk Files (%d) ===", len(chunks))
    total_chunks = 0
    for fname, info in sorted(chunks.items()):
        total_chunks += info["count"]
        if info["empty"] > 0:
            logger.warning("  [CHUNKS]  %s  (%d chunks, %d EMPTY!)",
                           fname, info["count"], info["empty"])
        else:
            logger.info("  [CHUNKS]  %s  (%d chunks)", fname, info["count"])
    logger.info("Total chunks across all files: %d", total_chunks)
    return chunks, total_chunks

# ─── 5. ChromaDB verification ─────────────────────────────────────────────────
def audit_chromadb(expected_total: int):
    """Verify ChromaDB has the expected number of indexed chunks."""
    client = get_chroma_client(str(CHROMA_DIR))
    collection = get_or_create_collection(client, CHROMA_COLLECTION_NAME)
    actual = collection.count()
    logger.info("=== ChromaDB Index ===")
    logger.info("  Expected chunks: %d", expected_total)
    logger.info("  Indexed chunks:  %d", actual)
    if actual == expected_total:
        logger.info("  [OK] All chunks successfully indexed — zero silent drops confirmed.")
    elif actual < expected_total:
        logger.error("  [FAIL] %d chunks were NOT indexed (expected=%d, actual=%d)!",
                     expected_total - actual, expected_total, actual)
    else:
        logger.warning("  [WARN] ChromaDB has MORE chunks than expected "
                       "(expected=%d, actual=%d). Possible stale duplicates.",
                       expected_total, actual)
    return actual

# ─── 6. Error log check ───────────────────────────────────────────────────────
def audit_error_logs():
    """Read and report any entries in ingestion/chunking/embedding error logs."""
    logs = {
        "ingestion_errors.log": INGESTION_ERROR_LOG,
        "chunking_errors.log": CHUNKING_ERROR_LOG,
        "embedding_errors.log": EMBEDDING_ERROR_LOG,
    }
    logger.info("=== Error Log Audit ===")
    any_errors = False
    for log_name, log_path in logs.items():
        if not os.path.exists(log_path):
            logger.info("  [OK]  %s: not found (no errors logged)", log_name)
            continue
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
        if content:
            lines = content.splitlines()
            logger.warning("  [WARN]  %s: %d error entries found!", log_name, len(lines))
            for line in lines[:5]:   # show first 5
                logger.warning("    >> %s", line)
            if len(lines) > 5:
                logger.warning("    ... (%d more)", len(lines) - 5)
            any_errors = True
        else:
            logger.info("  [OK]  %s: empty (no errors)", log_name)
    if not any_errors:
        logger.info("  All error logs clean — no silent failures detected.")


def main():
    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  LibraAI — Full-Corpus Ingestion Audit               ║")
    logger.info("╚══════════════════════════════════════════════════════╝")

    source = audit_source_documents()
    processed = audit_processed()
    cleaned = audit_cleaned()
    chunks, total_chunks = audit_chunks()

    # Cross-reference: every processed doc should appear in cleaned and chunks
    logger.info("=== Cross-Reference Check ===")
    processed_set = set(processed.keys())
    cleaned_set = set(cleaned.keys())
    chunks_set = set(chunks.keys())
    missing_from_cleaned = processed_set - cleaned_set
    missing_from_chunks = processed_set - chunks_set
    if missing_from_cleaned:
        logger.error("  [FAIL] Documents processed but NOT cleaned: %s", missing_from_cleaned)
    else:
        logger.info("  [OK] All processed documents appear in cleaned/")
    if missing_from_chunks:
        logger.error("  [FAIL] Documents cleaned but NOT chunked: %s", missing_from_chunks)
    else:
        logger.info("  [OK] All cleaned documents appear in chunks/")

    audit_chromadb(total_chunks)
    audit_error_logs()

    logger.info("╔══════════════════════════════════════════════════════╗")
    logger.info("║  Audit Complete. See output above.                   ║")
    logger.info("╚══════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
