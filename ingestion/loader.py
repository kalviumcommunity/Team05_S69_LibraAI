import os
import json
import logging
import fitz  # PyMuPDF

# Configure logging for ingestion errors
logging.basicConfig(
    filename='ingestion_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_pdf(filepath):
    pages = []
    try:
        doc = fitz.open(filepath)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            pages.append({
                "page_number": page_num + 1,
                "text": text,
                "doc_title": os.path.basename(filepath),
                "source_path": filepath
            })
    except Exception as e:
        logging.error(f"Failed to load PDF {filepath}: {str(e)}")
        raise
    return pages

def load_text(filepath):
    pages = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            # Text/Markdown files don't have native pages, treat as single page
            pages.append({
                "page_number": 1,
                "text": text,
                "doc_title": os.path.basename(filepath),
                "source_path": filepath
            })
    except Exception as e:
        logging.error(f"Failed to load Text {filepath}: {str(e)}")
        raise
    return pages

def process_documents(data_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if not os.path.isfile(filepath):
            continue

        ext = os.path.splitext(filename)[1].lower()
        pages = []
        
        try:
            if ext == '.pdf':
                pages = load_pdf(filepath)
            elif ext in ['.txt', '.md', '.csv']:
                pages = load_text(filepath)
            else:
                logging.error(f"Unsupported file format {filepath}")
                continue
                
            if pages:
                output_file = os.path.join(output_dir, f"{filename}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(pages, f, indent=4, ensure_ascii=False)
                print(f"Processed {filename} -> {output_file}")
                
        except Exception as e:
            # The specific loaders already log the error, but we catch it here to prevent the pipeline from crashing
            print(f"Error processing {filename}. See ingestion_errors.log for details.")

if __name__ == "__main__":
    process_documents("data", os.path.join("data", "processed"))
