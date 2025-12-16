# step3_create_embeddings_hybrid.py
import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch
import numpy as np
from datetime import datetime
from rank_bm25 import BM25Okapi
import pickle
import nltk
from nltk.tokenize import word_tokenize

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# FAST MODEL FOR STAGE 1 RETRIEVAL
EMBEDDING_MODEL = "intfloat/e5-small-v2"  # Fastest with good accuracy
BATCH_SIZE = 64
CHROMA_DB_PATH = "chroma_db"
BM25_INDEX_PATH = "bm25_index.pkl"
COLLECTION_NAME = "medical_textbooks"
INPUT_DIR = "processed_chunks"
LOG_FILE = "logs/embedding_log.json"

print("=" * 70)
print("STEP 3: HYBRID EMBEDDING SYSTEM (BM25 + VECTOR)")
print("=" * 70)
print(f"\nVector Model: {EMBEDDING_MODEL}")
print(f"Keyword Model: BM25")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device.upper()}")

# Load fast embedding model
print(f"\nLoading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL, device=device)
if device == "cuda":
    model.half()  # FP16 optimization
print(f"Model loaded - Dimension: {model.get_sentence_embedding_dimension()}")

# Initialize ChromaDB
print(f"\nInitializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

try:
    chroma_client.delete_collection(name=COLLECTION_NAME)
    print(f"Deleted existing collection")
except:
    pass

collection = chroma_client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
print(f"Collection created: {COLLECTION_NAME}")

# Load all chunks
chunked_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('_chunked.json')]
print(f"\nFound {len(chunked_files)} chunked files")

all_chunks = []
all_texts = []

for chunked_file in chunked_files:
    with open(os.path.join(INPUT_DIR, chunked_file), 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)
        all_chunks.extend(chunks_data)
        all_texts.extend([chunk['text'] for chunk in chunks_data])

print(f"Total chunks loaded: {len(all_chunks)}")

# CREATE BM25 INDEX
print(f"\n{'=' * 70}")
print("Creating BM25 Index...")
print(f"{'=' * 70}")

tokenized_corpus = [word_tokenize(text.lower()) for text in tqdm(all_texts, desc="Tokenizing")]
bm25 = BM25Okapi(tokenized_corpus)

# Save BM25 index
with open(BM25_INDEX_PATH, 'wb') as f:
    pickle.dump({'bm25': bm25, 'corpus': all_texts, 'chunks': all_chunks}, f)
print(f"✓ BM25 index saved: {BM25_INDEX_PATH}")

# CREATE VECTOR EMBEDDINGS
print(f"\n{'=' * 70}")
print("Creating Vector Embeddings...")
print(f"{'=' * 70}")

ids = [chunk['id'] for chunk in all_chunks]
metadatas = [{
    'source': chunk['source'],
    'chunk_index': chunk['chunk_index'],
    'char_count': chunk['char_count']
} for chunk in all_chunks]

all_embeddings = []
for i in tqdm(range(0, len(all_texts), BATCH_SIZE), desc="Batches"):
    batch_texts = all_texts[i:i+BATCH_SIZE]
    batch_embeddings = model.encode(
        batch_texts,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    all_embeddings.extend(batch_embeddings.tolist())

print(f"✓ Embeddings generated: {len(all_embeddings)}")

# Add to ChromaDB
collection.add(
    ids=ids,
    embeddings=all_embeddings,
    documents=all_texts,
    metadatas=metadatas
)
print(f"✓ Added to ChromaDB: {collection.count()} chunks")

print(f"\n{'=' * 70}")
print("EMBEDDING CREATION COMPLETE")
print(f"{'=' * 70}")
print(f"Vector DB: {CHROMA_DB_PATH}")
print(f"BM25 Index: {BM25_INDEX_PATH}")
print(f"Total chunks: {len(all_chunks):,}")
print(f"{'=' * 70}\n")
