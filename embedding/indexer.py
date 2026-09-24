import os
import json
import logging
from typing import List, Dict, Any
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

logging.basicConfig(
    filename='embedding_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_embeddings():
    # Fallback to bge-small-en as requested for local/free setup
    model_name = "BAAI/bge-small-en-v1.5"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    return HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

def index_chunks(chunks_dir: str, persist_directory: str, sample_only: bool = True):
    embeddings = create_embeddings()
    docs = []
    
    # Process only a few sample documents if sample_only is True
    processed_count = 0
    for filename in os.listdir(chunks_dir):
        if not filename.endswith('.json'):
            continue
            
        if sample_only and "sample_doc" not in filename:
            # We want to run this on a small sample set first
            continue
            
        filepath = os.path.join(chunks_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            chunk_records = json.load(f)
            
        for record in chunk_records:
            metadata = {
                "chunk_id": record.get("chunk_id"),
                "doc_title": record.get("doc_title"),
                "source_path": record.get("source_path"),
                "page_number": record.get("page_number", 1),
                "is_reference_section": str(record.get("is_reference_section", False))
            }
            # Langchain expects metadata values to be str, int, float, or bool.
            doc = Document(page_content=record["text"], metadata=metadata)
            docs.append(doc)
            
        processed_count += 1
        print(f"Loaded {len(chunk_records)} chunks from {filename}")
        
    print(f"Total documents to embed: {len(docs)}")
    
    # Initialize Chroma and persist
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    return vectorstore

def verify_query(vectorstore, query: str):
    print(f"\n--- Verifying Query: '{query}' ---")
    results = vectorstore.similarity_search(query, k=2)
    for i, doc in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Metadata: {doc.metadata}")
        print(f"Content snippet: {doc.page_content[:150]}...")

if __name__ == "__main__":
    chunks_dir = os.path.join("data", "chunks")
    persist_dir = os.path.join("data", "chroma_db")
    
    # 1. Index a small sample set
    print("Indexing sample documents...")
    vectorstore = index_chunks(chunks_dir, persist_dir, sample_only=False)
    
    # 2. Verify with a test query
    verify_query(vectorstore, "What is Artificial Intelligence in Libraries?")
    verify_query(vectorstore, "How to proceed with the new system guidelines?")
