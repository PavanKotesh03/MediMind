# step4_query_system_hybrid.py
# ===========================
# Hybrid BM25 + Vector + Reranker Retrieval
# - Silent when imported (for LLM)
# - Verbose only in CLI debug mode

import os
import time
import pickle
import nltk
import torch
import chromadb
import numpy as np
from typing import List, Dict
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer, CrossEncoder

# -------------------------------------------------------------------
# NLTK SETUP
# -------------------------------------------------------------------
for resource in ["punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{resource}")
    except LookupError:
        nltk.download(resource)

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
VERBOSE = False  # MUST be False when imported by LLM

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BM25_INDEX_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "bm25_index.pkl")
)

CHROMA_DB_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "chroma_db")
)

COLLECTION_NAME = "medical_textbooks"

FAST_MODEL = "intfloat/e5-small-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

VECTOR_TOP_K = 30
BM25_TOP_K = 30
RERANK_TOP_K = 100
FINAL_RESULTS = 10
MIN_SCORE = 0.15

VECTOR_WEIGHT = 0.4
BM25_WEIGHT = 0.6
print(" step4_query_system_hybrid.py LOADED FROM:", __file__)

# -------------------------------------------------------------------
# MEDICAL QUERY EXPANSION
# -------------------------------------------------------------------
MEDICAL_SYNONYMS = {
    "fever": ["pyrexia", "febrile", "temperature", "hyperthermia"],
    "cough": ["tussis", "coughing"],
    "headache": ["cephalgia", "head pain"],
    "body pain": ["myalgia", "body ache", "flu"],
    "shortness of breath": ["dyspnea", "breathlessness"],
}

SYMPTOM_TO_CONDITIONS = {
    "fever": ["viral infection", "bacterial infection", "inflammation"],
    "body pain": ["viral fever", "influenza", "myalgia"],
    "headache": ["migraine", "tension headache"],
}

# -------------------------------------------------------------------
# LOAD MODELS (ONCE)
# -------------------------------------------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"

fast_model = SentenceTransformer(FAST_MODEL, device=device)
if device == "cuda":
    fast_model.half()

reranker = CrossEncoder(RERANK_MODEL, device=device)

# -------------------------------------------------------------------
# LOAD BM25
# -------------------------------------------------------------------
with open(BM25_INDEX_PATH, "rb") as f:
    bm25_data = pickle.load(f)
    bm25 = bm25_data["bm25"]
    corpus = bm25_data["corpus"]
    chunks = bm25_data["chunks"]

# -------------------------------------------------------------------
# LOAD CHROMA
# -------------------------------------------------------------------
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_collection(name=COLLECTION_NAME)

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
def expand_query(query: str) -> str:
    query_lower = query.lower()
    expanded = [query]

    for k, v in MEDICAL_SYNONYMS.items():
        if k in query_lower:
            expanded.extend(v)

    for k, v in SYMPTOM_TO_CONDITIONS.items():
        if k in query_lower:
            expanded.extend(v)

    return " ".join(dict.fromkeys(expanded))


def normalize(scores: List[float]) -> List[float]:
    if not scores or max(scores) == min(scores):
        return [0.5] * len(scores)
    mn, mx = min(scores), max(scores)
    return [(s - mn) / (mx - mn) for s in scores]

# -------------------------------------------------------------------
# 🔥 MAIN API — USED BY LLM
# -------------------------------------------------------------------
def hybrid_search(query: str, top_k: int = FINAL_RESULTS) -> List[Dict]:
    """
    SILENT hybrid search function.
    This is what your LLM uses.
    """
    start = time.time()

    expanded_query = expand_query(query)

    # ---------------- BM25 ----------------
    tokens = word_tokenize(expanded_query.lower())
    bm25_scores = bm25.get_scores(tokens)
    bm25_idx = np.argsort(bm25_scores)[::-1][:BM25_TOP_K]

    bm25_results = {
        i: {
            "text": corpus[i],
            "metadata": chunks[i],
            "bm25_score": float(bm25_scores[i]),
        }
        for i in bm25_idx
    }

    # ---------------- VECTOR ----------------
    vec = collection.query(
        query_texts=[expanded_query],
        n_results=VECTOR_TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    vector_results = {}
    for i, text in enumerate(vec["documents"][0]):
        try:
            idx = corpus.index(text)
            vector_results[idx] = {
                "vector_score": 1 - vec["distances"][0][i]
            }
        except ValueError:
            continue

    # ---------------- COMBINE ----------------
    all_idx = set(bm25_results) | set(vector_results)

    bm25_norm = normalize(
        [bm25_results.get(i, {"bm25_score": 0})["bm25_score"] for i in all_idx]
    )
    vec_norm = normalize(
        [vector_results.get(i, {"vector_score": 0})["vector_score"] for i in all_idx]
    )

    combined = []
    for n, i in enumerate(all_idx):
        combined.append({
            "text": corpus[i],
            "metadata": chunks[i],
            "hybrid_score": (
                BM25_WEIGHT * bm25_norm[n] + VECTOR_WEIGHT * vec_norm[n]
            ),
        })

    combined.sort(key=lambda x: x["hybrid_score"], reverse=True)
    combined = combined[:RERANK_TOP_K]

    # ---------------- RERANK ----------------
    pairs = [[query, c["text"]] for c in combined]
    scores = reranker.predict(pairs, show_progress_bar=False)

    for i, c in enumerate(combined):
        c["rerank_score"] = float(scores[i])

    combined.sort(key=lambda x: x["rerank_score"], reverse=True)

    final = [
        c for c in combined
        if c["rerank_score"] > MIN_SCORE
    ][:top_k]

    if VERBOSE:
        print(f"Hybrid search took {(time.time() - start)*1000:.0f} ms")

    return final

# -------------------------------------------------------------------
# 🧪 CLI DEBUG MODE ONLY
# -------------------------------------------------------------------
if __name__ == "__main__":
    VERBOSE = True

    print("=" * 70)
    print("ADVANCED MEDICAL RAG SYSTEM (DEBUG MODE)")
    print("=" * 70)

    while True:
        q = input("\nQuery: ").strip()
        if q.lower() in ("exit", "quit", "q"):
            break

        results = hybrid_search(q)

        print("\nTop Results:\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r['text'][:300]}")
            print("-" * 60)
