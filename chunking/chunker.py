import os
import json
import logging
import re
import sys
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.corpus_catalog import get_document_catalog_entry

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

def extract_section_title(text: str, default_section: str = "General") -> str:
    """Extract section heading from text if present."""
    patterns = [
        r'(?m)^(#{1,4}\s+[^\n]+)',
        r'(?m)^([IVXLCDM]+\.\s+[^\n]+)',
        r'(?m)^(\d+\.\d*\s+[^\n]+)',
        r'(?m)^(Step\s+\d+[:\s\w—-]*)',
        r'(?m)^(Question\s+\d+[:\s\w—-]*)',
        r'(?m)^(Table\s+[IVX\d]+[:\s\w—-]*)',
        r'(?m)^(Appendix\s+[A-Z][:\s\w—-]*)',
        r'(?m)^(Section\s+\w+[:\s\w—-]*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            heading = match.group(1).strip().lstrip("#").strip()
            if 3 < len(heading) < 80:
                return heading
    return default_section

def chunk_documents(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    chunker = create_chunker()
    encoder = tiktoken.get_encoding("cl100k_base")
    
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            pages = json.load(f)
            
        catalog = get_document_catalog_entry(filename)
        doc_slug = catalog.get("doc_slug", filename.replace(".json", ""))
        doc_title = catalog.get("doc_title", filename)
        doc_type = catalog.get("doc_type", "other")
        author = catalog.get("author", "Unknown")
        course_code = catalog.get("course_code")
        
        document_chunks = []
        chunk_id_counter = 1
        current_section = "General"
        
        for page in pages:
            text = page.get("text", "")
            if not text.strip():
                continue
                
            page_num = page.get("page_number", 1)
            is_ref = page.get("is_reference_section", False)
            source_path = page.get("source_path", os.path.join("data", filename.replace(".json", "")))
            
            # Detect section from page level if available
            page_section = extract_section_title(text, current_section)
            if page_section != "General":
                current_section = page_section

            chunks = chunker.split_text(text)
            
            for chunk_text in chunks:
                chunk_section = extract_section_title(chunk_text, current_section)
                if chunk_section != "General":
                    current_section = chunk_section

                tokens = len(encoder.encode(chunk_text))
                chunk_id = f"{doc_slug}_p{page_num}_c{chunk_id_counter:03d}"
                
                chunk_record = {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "doc_title": doc_title,
                    "doc_type": doc_type,
                    "author": author,
                    "course_code": course_code,
                    "section": chunk_section,
                    "page_number": int(page_num),
                    "source_path": source_path,
                    "is_reference": bool(is_ref),
                    "token_count": tokens,
                    # Backward compatibility fields
                    "is_reference_section": bool(is_ref),
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

