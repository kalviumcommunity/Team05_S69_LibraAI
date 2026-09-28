"""
LibraAI - Vector Database Indexing Module
Day 5 Deliverable: ChromaDB Collection Indexer
Reference: PRD §6.2, §6.3, Appendix B, FR-04, FR-06
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
import chromadb
from chromadb.utils import embedding_functions

# Ensure root directory is on sys.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.schema import ChunkMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("libraai.indexer")

DEFAULT_CHROMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db"))
DEFAULT_COLLECTION_NAME = "libra_ai_corpus"


def get_embedding_function(api_key: Optional[str] = None):
    """
    Returns the appropriate embedding function:
    - OpenAI text-embedding-3-small if OPENAI_API_KEY is provided
    - Local Chroma DefaultEmbeddingFunction (all-MiniLM-L6-v2 ONNX) as robust offline default
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if key and key.strip() and not key.startswith("sk-placeholder"):
        logger.info("Using OpenAI text-embedding-3-small embedding function.")
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=key,
            model_name="text-embedding-3-small"
        )
    else:
        logger.info("Using ChromaDB local DefaultEmbeddingFunction (all-MiniLM-L6-v2).")
        return embedding_functions.DefaultEmbeddingFunction()


def get_chroma_client(persist_dir: str = DEFAULT_CHROMA_DIR) -> chromadb.PersistentClient:
    """Initialize and return a ChromaDB PersistentClient."""
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)


def get_or_create_collection(
    client: chromadb.PersistentClient,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_fn = None
) -> chromadb.Collection:
    """Get or create the ChromaDB collection configured with cosine space."""
    if embedding_fn is None:
        embedding_fn = get_embedding_function()

    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )


def load_chunks_from_directory(chunks_dir: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Load all chunk records from the chunks directory.
    Returns list of tuples: (chunk_id, text, chroma_metadata)
    """
    if not os.path.exists(chunks_dir):
        logger.error(f"Chunks directory does not exist: {chunks_dir}")
        return []

    records = []
    seen_ids = set()

    for filename in sorted(os.listdir(chunks_dir)):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(chunks_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                chunk_list = json.load(f)

            for chunk_dict in chunk_list:
                # Validate & parse through Pydantic ChunkMetadata
                meta = ChunkMetadata(
                    chunk_id=chunk_dict.get("chunk_id", f"{filename}_chunk_{len(records)}"),
                    doc_title=chunk_dict.get("doc_title", filename),
                    doc_type=chunk_dict.get("doc_type", "other"),
                    author=chunk_dict.get("author", "Unknown"),
                    course_code=chunk_dict.get("course_code"),
                    section=chunk_dict.get("section", "General"),
                    page_number=int(chunk_dict.get("page_number", 1)),
                    source_path=chunk_dict.get("source_path", ""),
                    is_reference=bool(chunk_dict.get("is_reference", False)),
                    token_count=int(chunk_dict.get("token_count", 0)),
                )

                chunk_id = meta.chunk_id
                if chunk_id in seen_ids:
                    # Guarantee unique ID
                    chunk_id = f"{chunk_id}_{len(records)}"
                seen_ids.add(chunk_id)

                text = chunk_dict.get("text", "").strip()
                if not text:
                    continue

                chroma_meta = meta.to_chroma_metadata()
                chroma_meta["chunk_id"] = chunk_id  # ensure sync
                records.append((chunk_id, text, chroma_meta))

        except Exception as e:
            logger.error(f"Error reading chunk file {filepath}: {e}")

    return records


def index_corpus(
    chunks_dir: Optional[str] = None,
    persist_dir: str = DEFAULT_CHROMA_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    batch_size: int = 50,
) -> int:
    """
    Index all chunks from chunks_dir into ChromaDB.
    Returns total number of chunks indexed.
    """
    if chunks_dir is None:
        chunks_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chunks"))

    logger.info(f"Loading chunks from: {chunks_dir}")
    records = load_chunks_from_directory(chunks_dir)
    logger.info(f"Loaded {len(records)} chunks for indexing.")

    if not records:
        logger.warning("No chunks found to index.")
        return 0

    client = get_chroma_client(persist_dir)
    embedding_fn = get_embedding_function()
    collection = get_or_create_collection(client, collection_name, embedding_fn)

    # Batch upsert to ChromaDB
    total_indexed = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        ids = [r[0] for r in batch]
        documents = [r[1] for r in batch]
        metadatas = [r[2] for r in batch]

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        total_indexed += len(batch)
        logger.info(f"Indexed batch {i // batch_size + 1}: {total_indexed}/{len(records)} chunks.")

    logger.info(f"Successfully indexed {total_indexed} chunks into ChromaDB at {persist_dir}.")
    return total_indexed


if __name__ == "__main__":
    index_corpus()
