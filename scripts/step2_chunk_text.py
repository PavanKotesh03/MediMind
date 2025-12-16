# step2_chunk_text_optimized.py
import os
import json
from pathlib import Path
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

# OPTIMIZED CONFIGURATION
CHUNK_SIZE = 1000  # Reduced from 2500 for better symptom isolation
CHUNK_OVERLAP = 200  # Reduced from 500
MIN_CHUNK_SIZE = 300  # Lower minimum to keep more medical content

# Use absolute paths for consistency
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
INPUT_DIR = str(PROJECT_ROOT / "processed_chunks")
OUTPUT_DIR = str(PROJECT_ROOT / "processed_chunks")
LOG_FILE = str(PROJECT_ROOT / "logs/chunking_log.json")

# Enhanced medical keywords
MEDICAL_KEYWORDS = [
    'symptom', 'symptoms', 'presentation', 'clinical features',
    'signs', 'complaint', 'history', 'patient presents',
    'diagnosis', 'differential', 'assessment', 'evaluation',
    'manifestation', 'finding', 'examination', 'disease',
    'condition', 'syndrome', 'disorder', 'treatment',
    'pain', 'fever', 'cough', 'breathing', 'chest',
    'acute', 'chronic', 'severe', 'mild', 'moderate'
]

EXCLUDE_PATTERNS = [
    r'Figure\s+\d+', r'Table\s+\d+', r'Image\s+\d+',
    r'Diagram\s+\d+', r'^\d+\.\d+\s+\d+\.\d+',
    r'Copyright', r'ISBN', r'DOI:'
]

def is_valid_chunk(chunk):
    """Enhanced validation with medical content detection"""
    chunk_lower = chunk.lower()
    
    # Exclude non-medical content
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, chunk, re.IGNORECASE):
            return False
    
    # Must have substantial text
    if sum(c.isalpha() for c in chunk) < len(chunk) * 0.5:
        return False
    
    words = chunk.split()
    if len(words) < 30:  # Lowered from 20
        return False
    
    # Check for medical content (more lenient)
    has_medical_content = any(kw in chunk_lower for kw in MEDICAL_KEYWORDS)
    
    # Accept if has medical keywords OR is substantive text
    return has_medical_content or len(words) > 80

print("=" * 70)
print("STEP 2: OPTIMIZED CHUNKING FOR MEDICAL RAG")
print("=" * 70)
print(f"\nConfiguration:")
print(f"Chunk size: {CHUNK_SIZE} characters")
print(f"Overlap: {CHUNK_OVERLAP} characters")
print(f"Min size: {MIN_CHUNK_SIZE} characters")

# Semantic-aware splitters (respects medical structure)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    separators=["\n\n\n", "\n\n", "\n", ". ", "; ", ", ", " ", ""]  # Enhanced
)

txt_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('_extracted.txt')]
print(f"\nFound {len(txt_files)} extracted text files")

chunking_log = {
    'timestamp': datetime.now().isoformat(),
    'config': {
        'chunk_size': CHUNK_SIZE,
        'chunk_overlap': CHUNK_OVERLAP,
        'min_chunk_size': MIN_CHUNK_SIZE
    },
    'results': []
}

total_chunks = 0

for txt_file in txt_files:
    print(f"\n{'=' * 70}")
    print(f"Processing: {txt_file}")
    print(f"{'=' * 70}")
    
    input_path = os.path.join(INPUT_DIR, txt_file)
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"Original text: {len(text):,} characters")
        
        raw_chunks = text_splitter.split_text(text)
        print(f"Raw chunks created: {len(raw_chunks)}")
        
        # Filter chunks
        filtered_chunks = [chunk for chunk in raw_chunks 
                          if len(chunk) >= MIN_CHUNK_SIZE and is_valid_chunk(chunk)]
        
        print(f"After filtering: {len(filtered_chunks)} chunks")
        
        # Create metadata
        chunks_with_metadata = []
        for i, chunk in enumerate(filtered_chunks):
            chunks_with_metadata.append({
                'id': f"{Path(txt_file).stem}_chunk_{i}",
                'text': chunk,
                'source': txt_file.replace('_extracted.txt', '.pdf'),
                'chunk_index': i,
                'total_chunks': len(filtered_chunks),
                'char_count': len(chunk)
            })
        
        output_file = os.path.join(OUTPUT_DIR, f"{Path(txt_file).stem}_chunked.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_with_metadata, f, indent=2, ensure_ascii=False)
        
        total_chunks += len(filtered_chunks)
        
        chunking_log['results'].append({
            'file': txt_file,
            'chunks': len(filtered_chunks),
            'output': output_file,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        chunking_log['results'].append({
            'file': txt_file,
            'status': 'failed',
            'error': str(e)
        })

chunking_log['total_chunks'] = total_chunks
with open(LOG_FILE, 'w', encoding='utf-8') as f:
    json.dump(chunking_log, f, indent=2)

print(f"\n{'=' * 70}")
print("CHUNKING SUMMARY")
print(f"{'=' * 70}")
print(f"Total chunks: {total_chunks:,}")
print(f"Log saved: {LOG_FILE}")
print(f"{'=' * 70}\n")
