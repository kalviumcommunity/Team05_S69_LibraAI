import os
import json
import logging
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(
    filename='chunking_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_chunker():
    # Use standard text-embedding-3-small tokenizer
    # 400 tokens chunk size, 15% overlap = 60 tokens
    # Separators prioritize section breaks, then paragraphs, then lines, etc.
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=400,
        chunk_overlap=60,
        separators=[
            "\n\n## ", "\n\n### ", "\n\n", "\n", " ", ""
        ]
    )

def chunk_documents(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    chunker = create_chunker()
    
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            pages = json.load(f)
            
        document_chunks = []
        chunk_id_counter = 1
        
        # We can either chunk page by page, or group all text and chunk.
        # Since we want section boundaries across pages, it's better to process
        # the whole document if possible, but we need to retain page metadata.
        # A simple way: chunk per page, but this might split sections at page breaks.
        # For MVP, chunking per page with metadata attached is standard and preserves page numbers.
        for page in pages:
            text = page.get("text", "")
            if not text.strip():
                continue
                
            # If it's a reference section and we want to exclude or tag it, we have that metadata
            # We chunk the text
            chunks = chunker.split_text(text)
            
            for chunk_text in chunks:
                chunk_record = {
                    "chunk_id": f"{filename}_chunk_{chunk_id_counter}",
                    "text": chunk_text,
                    "doc_title": page.get("doc_title"),
                    "source_path": page.get("source_path"),
                    "page_number": page.get("page_number"),
                    "is_reference_section": page.get("is_reference_section", False)
                }
                document_chunks.append(chunk_record)
                chunk_id_counter += 1
                
        output_file = os.path.join(output_dir, filename)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(document_chunks, f, indent=4, ensure_ascii=False)
        print(f"Chunked {filename} -> {len(document_chunks)} chunks.")

if __name__ == "__main__":
    input_dir = os.path.join("data", "cleaned")
    output_dir = os.path.join("data", "chunks")
    chunk_documents(input_dir, output_dir)
