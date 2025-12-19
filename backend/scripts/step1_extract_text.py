import os
import json
import PyPDF2
from pathlib import Path
from datetime import datetime
import re

BOOKS_DIR = "books"
OUTPUT_DIR = "processed_chunks"
LOG_FILE = "logs/extraction_log.json"

# Common header/footer patterns to remove
HEADER_FOOTER_PATTERNS = [
    r'^\d+\s*$',  # Page numbers alone
    r'^Page\s+\d+',  # "Page 123"
    r'^\d+\s+of\s+\d+',  # "1 of 500"
    r'^Chapter\s+\d+',  # "Chapter 5"
    r'Copyright.*\d{4}',  # Copyright lines
    r'All rights reserved',
    r'^www\.',  # URLs
    r'^http',
]

# Non-English text patterns (Hindi, Arabic, etc.)
NON_ENGLISH_PATTERN = r'[\u0900-\u097F\u0600-\u06FF\u0980-\u09FF]'

def is_header_footer(line):
    line = line.strip()
    if len(line) < 5:
        return True
    for pattern in HEADER_FOOTER_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def remove_non_english(text):
    return re.sub(NON_ENGLISH_PATTERN, '', text)

def clean_text(text):
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip headers/footers
        if is_header_footer(line):
            continue
        
        # Remove non-English characters
        line = remove_non_english(line)
        
        # Skip lines that are too short after cleaning
        if len(line.strip()) < 10:
            continue
        
        # Skip lines that are mostly numbers (likely tables)
        if sum(c.isdigit() for c in line) > len(line) * 0.5:
            continue
        
        cleaned_lines.append(line)
    
    # Join and clean extra whitespace
    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
    
    return cleaned_text

print("=" * 70)
print("STEP 1: TEXT EXTRACTION WITH FILTERING")
print("=" * 70)
print("\nFilters applied:")
print("- Headers and footers removed")
print("- Non-English text removed")
print("- Image text ignored")
print("- Table numbers filtered")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

pdf_files = [f for f in os.listdir(BOOKS_DIR) if f.endswith('.pdf')]
print(f"\nFound {len(pdf_files)} PDF files to process")

extraction_log = {
    'timestamp': datetime.now().isoformat(),
    'total_pdfs': len(pdf_files),
    'results': []
}

for pdf_file in pdf_files:
    print(f"\n{'=' * 70}")
    print(f"Processing: {pdf_file}")
    print(f"{'=' * 70}")
    
    pdf_path = os.path.join(BOOKS_DIR, pdf_file)
    
    try:
        raw_text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            print(f"Total pages: {total_pages}")
            
            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    raw_text += page_text + "\n"
                except:
                    # Skip pages that fail to extract
                    continue
                
                if (i + 1) % 50 == 0:
                    print(f"Extracted: {i + 1}/{total_pages} pages")
        
        print(f"Raw extraction complete: {len(raw_text):,} characters")
        
        # Clean the text
        print("Applying filters...")
        cleaned_text = clean_text(raw_text)
        
        print(f"After filtering: {len(cleaned_text):,} characters")
        reduction = ((len(raw_text) - len(cleaned_text)) / len(raw_text)) * 100
        print(f"Filtered out: {reduction:.1f}% of content")
        
        output_file = os.path.join(OUTPUT_DIR, f"{Path(pdf_file).stem}_extracted.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        extraction_log['results'].append({
            'file': pdf_file,
            'pages': total_pages,
            'raw_characters': len(raw_text),
            'cleaned_characters': len(cleaned_text),
            'filtered_percentage': round(reduction, 2),
            'output': output_file,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        extraction_log['results'].append({
            'file': pdf_file,
            'status': 'failed',
            'error': str(e)
        })

with open(LOG_FILE, 'w', encoding='utf-8') as f:
    json.dump(extraction_log, f, indent=2)

print(f"\n{'=' * 70}")
print("EXTRACTION SUMMARY")
print(f"{'=' * 70}")
successful = sum(1 for r in extraction_log['results'] if r['status'] == 'success')
print(f"Successful: {successful}/{len(pdf_files)}")
total_filtered = sum(r.get('filtered_percentage', 0) for r in extraction_log['results'] if r['status'] == 'success')
avg_filtered = total_filtered / successful if successful > 0 else 0
print(f"Average content filtered: {avg_filtered:.1f}%")
print(f"Log saved: {LOG_FILE}")
print(f"{'=' * 70}\n")
