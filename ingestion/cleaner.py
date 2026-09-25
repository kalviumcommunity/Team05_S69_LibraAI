import os
import json
import re

def normalize_encoding(text):
    # Normalize ligatures and invisible characters from PDF extraction
    ligatures = {
        '\ufb00': 'ff',
        '\ufb01': 'fi',
        '\ufb02': 'fl',
        '\ufb03': 'ffi',
        '\ufb04': 'ffl',
        '\u200b': '',  # zero-width space
        '\u200c': '',  # zero-width non-joiner
        '\u00a0': ' ', # non-breaking space
    }
    for char, rep in ligatures.items():
        text = text.replace(char, rep)
    return text

def normalize_whitespace(text):
    # Normalize encoding & ligatures first
    text = normalize_encoding(text)
    # Fix hyphenated line breaks
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    # Replace multiple spaces with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def strip_headers_footers(text):
    lines = text.split('\n')
    cleaned_lines = []
    # Very simple heuristic: remove lines containing "Header" or "Footer" or "Page" 
    # if they appear at the very top or bottom.
    # We will just filter out explicit mock headers/footers for this demo
    for line in lines:
        if re.search(r'(?i)(header|footer|page \d)', line):
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def detect_references(text):
    # Detect if text contains a reference/bibliography section
    ref_match = re.search(r'(?i)\n(references|bibliography)\n', text)
    if ref_match:
        return True
    return False

def clean_documents(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            pages = json.load(f)
            
        cleaned_pages = []
        for page in pages:
            text = page.get("text", "")
            
            # Step 1: Detect References
            is_ref = detect_references(text)
            page['is_reference_section'] = is_ref
            
            # Step 2: Strip headers/footers
            text = strip_headers_footers(text)
            
            # Step 3: Normalize whitespace
            text = normalize_whitespace(text)
            
            page['text'] = text.strip()
            cleaned_pages.append(page)
            
        output_file = os.path.join(output_dir, filename)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_pages, f, indent=4, ensure_ascii=False)
        print(f"Cleaned {filename} -> {output_file}")

if __name__ == "__main__":
    input_dir = os.path.join("data", "processed")
    output_dir = os.path.join("data", "cleaned")
    clean_documents(input_dir, output_dir)
