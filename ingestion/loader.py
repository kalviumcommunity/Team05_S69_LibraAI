import os
import json
import logging
import zipfile
import xml.etree.ElementTree as ET
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

def load_docx(filepath):
    pages = []
    try:
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        with zipfile.ZipFile(filepath) as z:
            tree = ET.fromstring(z.read('word/document.xml'))
            body = tree.find('w:body', namespaces)
            if body is None:
                return pages

            elements = []
            for child in body:
                tag = child.tag.split('}')[-1]
                if tag == 'p':
                    p_text = ''.join(t.text for t in child.iterfind('.//w:t', namespaces) if t.text)
                    if p_text.strip():
                        elements.append(p_text.strip())
                elif tag == 'tbl':
                    rows = []
                    for tr in child.iterfind('.//w:tr', namespaces):
                        row = []
                        for tc in tr.iterfind('.//w:tc', namespaces):
                            tc_text = ' '.join(t.text for t in tc.iterfind('.//w:t', namespaces) if t.text)
                            row.append(tc_text.strip())
                        if any(row):
                            rows.append(' | '.join(row))
                    if rows:
                        elements.append('\n'.join(rows))

        # Split elements into synthetic pages (approx 15 elements per synthetic page)
        batch_size = 15
        for i in range(0, max(len(elements), 1), batch_size):
            page_elements = elements[i : i + batch_size]
            page_text = "\n\n".join(page_elements)
            pages.append({
                "page_number": (i // batch_size) + 1,
                "text": page_text,
                "doc_title": os.path.basename(filepath),
                "source_path": filepath
            })
    except Exception as e:
        logging.error(f"Failed to load DOCX {filepath}: {str(e)}")
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
            elif ext == '.docx':
                pages = load_docx(filepath)
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

