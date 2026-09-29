import os
import sys
import logging
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

logging.basicConfig(level=logging.ERROR)

def create_embeddings():
    model_name = "BAAI/bge-small-en-v1.5"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    return HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

def main():
    if len(sys.argv) < 2:
        print("Usage: python query_test.py \"your question here\"")
        sys.exit(1)
        
    query = sys.argv[1]
    persist_dir = os.path.join("data", "chroma_db")
    
    if not os.path.exists(persist_dir):
        print(f"Error: ChromaDB directory '{persist_dir}' not found. Run indexer first.")
        sys.exit(1)
        
    print(f"Loading ChromaDB from {persist_dir}...")
    embeddings = create_embeddings()
    vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    
    print(f"\nQuery: {query}")
    print("-" * 50)
    
    # Retrieve top-k chunks
    k = 5
    results = vectorstore.similarity_search_with_score(query, k=k)
    
    if not results:
        print("No results found.")
        return
        
    for i, (doc, score) in enumerate(results):
        print(f"\n--- Result {i+1} (Score: {score:.4f}) ---")
        print(f"Document: {doc.metadata.get('doc_title')}")
        print(f"Page/Section: {doc.metadata.get('page_number')} | Reference: {doc.metadata.get('is_reference_section')}")
        snippet = doc.page_content[:300].encode('ascii', 'ignore').decode('ascii')
        print(f"Snippet: {snippet}...")

if __name__ == "__main__":
    main()
