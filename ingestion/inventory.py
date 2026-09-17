import os
import fitz  # PyMuPDF
import sys

def analyze_corpus(data_dir, output_file):
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist.")
        return
    
    total_docs = 0
    formats = {}
    total_length = 0
    scanned_pdfs = []
    
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if not os.path.isfile(filepath):
            continue
            
        total_docs += 1
        ext = os.path.splitext(filename)[1].lower()
        formats[ext] = formats.get(ext, 0) + 1
        
        if ext == '.pdf':
            try:
                doc = fitz.open(filepath)
                text = ""
                for page in doc:
                    text += page.get_text()
                
                doc_len = len(text)
                total_length += doc_len
                
                if doc_len < 100 and doc.page_count > 0: # Arbitrary small threshold for scanned PDFs
                    scanned_pdfs.append(filename)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        elif ext in ['.txt', '.md', '.csv', '.html']:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                    total_length += len(text)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                
    avg_length = total_length / total_docs if total_docs > 0 else 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Corpus Inventory Report\n\n")
        f.write(f"- **Total Documents:** {total_docs}\n")
        f.write("- **Formats:**\n")
        for ext, count in formats.items():
            f.write(f"  - {ext}: {count}\n")
        f.write(f"- **Average Document Length (characters):** {avg_length:.2f}\n")
        f.write(f"- **Likely Scanned PDFs (low extractable text):** {len(scanned_pdfs)}\n")
        for pdf in scanned_pdfs:
            f.write(f"  - {pdf}\n")

if __name__ == "__main__":
    analyze_corpus("data", "corpus_inventory.md")
