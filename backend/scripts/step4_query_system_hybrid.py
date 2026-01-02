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
RERANK_TOP_K = 60
FINAL_RESULTS = 6
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
#  MAIN API — USED BY LLM
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
# CLI DEBUG MODE ONLY
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

def retrieve_medical_context(query: str, top_k: int = 6) -> List[Dict]:
    """
    Wrapper function for easy import by other modules.
    This is what explanation_agent.py should use.
    """
    return hybrid_search(query)[:top_k]

# step4_query_system_hybrid.py - WITH DIAGNOSIS/TREATMENT FILTERING
# import chromadb
# from sentence_transformers import SentenceTransformer, CrossEncoder
# import torch
# import pickle
# from rank_bm25 import BM25Okapi
# from nltk.tokenize import word_tokenize
# import numpy as np
# from typing import List, Dict
# import time
# import sys
# from pathlib import Path


# # Add parent directory to Python path
# sys.path.insert(0, str(Path(__file__).parent.parent))


# # CONFIGURATION
# # Use absolute paths to ensure the files can be found regardless of working directory
# PROJECT_ROOT = Path(__file__).parent.parent.absolute()
# FAST_MODEL = "intfloat/e5-small-v2"
# RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
# CHROMA_DB_PATH = str(PROJECT_ROOT / "chroma_db")
# BM25_INDEX_PATH = str(PROJECT_ROOT / "bm25_index.pkl")
# COLLECTION_NAME = "medical_textbooks"


# # Retrieval parameters
# VECTOR_TOP_K = 20
# BM25_TOP_K = 20
# RERANK_TOP_K = 40
# FINAL_RESULTS = 5
# MIN_SCORE = 0.15  # Minimum relevance threshold


# # Hybrid weights
# VECTOR_WEIGHT = 0.5  # 50% semantic
# BM25_WEIGHT = 0.5    # 50% keyword


# # Medical synonyms for query expansion
# MEDICAL_SYNONYMS = {
#     'chest pain': ['angina', 'thoracic pain', 'chest discomfort', 'precordial pain', 'cardiac pain'],
#     'stomach pain': ['abdominal pain', 'gastric pain', 'belly pain', 'epigastric pain'],
#     'abdominal pain': ['stomach pain', 'belly pain', 'gastric pain', 'abdominal discomfort'],
#     'back pain': ['dorsal pain', 'lumbar pain', 'spinal pain'],
#     'headache': ['cephalgia', 'head pain', 'cranial pain', 'migraine'],
#     'breathing': ['respiration', 'dyspnea', 'breathlessness', 'respiratory'],
#     'shortness of breath': ['dyspnea', 'breathlessness', 'respiratory distress'],
#     'difficulty breathing': ['dyspnea', 'breathlessness', 'labored breathing'],
#     'fever': ['pyrexia', 'febrile', 'temperature', 'hyperthermia'],
#     'tired': ['fatigue', 'exhaustion', 'lethargy', 'weakness', 'asthenia'],
#     'weakness': ['fatigue', 'asthenia', 'lethargy'],
#     'dizzy': ['dizziness', 'vertigo', 'lightheaded'],
#     'nausea': ['nauseous', 'sick', 'queasy'],
#     'vomit': ['vomiting', 'emesis'],
#     'diarrhea': ['loose stools', 'frequent bowel movements'],
#     'cough': ['tussis', 'coughing'],
#     'pain': ['ache', 'discomfort', 'soreness'],
# }


# # Symptom to medical conditions mapping
# SYMPTOM_CONDITIONS = {
#     'stomach pain': ['gastritis', 'peptic ulcer', 'gastroenteritis', 'dyspepsia', 'GERD', 
#                      'gastric ulcer', 'duodenal ulcer', 'IBS', 'pancreatitis'],
#     'abdominal pain': ['appendicitis', 'gastritis', 'pancreatitis', 'cholecystitis', 
#                        'bowel obstruction', 'peptic ulcer', 'diverticulitis', 'IBS'],
#     'chest pain': ['angina', 'myocardial infarction', 'pericarditis', 'pulmonary embolism',
#                    'aortic dissection', 'costochondritis', 'GERD'],
#     'headache': ['migraine', 'tension headache', 'cluster headache', 'sinusitis', 'meningitis'],
#     'fever': ['infection', 'flu', 'pneumonia', 'typhoid', 'tuberculosis', 'malaria', 'sepsis', 'dengue'],
#     'cough': ['bronchitis', 'pneumonia', 'asthma', 'COPD', 'tuberculosis'],
#     'shortness of breath': ['asthma', 'COPD', 'pneumonia', 'heart failure', 'pulmonary embolism'],
#     'back pain': ['lumbar strain', 'sciatica', 'disc herniation', 'spondylosis', 'spinal stenosis'],
#     'leg pain': ['DVT', 'peripheral artery disease', 'sciatica', 'muscle strain'],
#     'joint pain': ['arthritis', 'rheumatoid arthritis', 'osteoarthritis', 'gout'],
#     'body pain': ['flu', 'fibromyalgia', 'viral infection', 'polymyalgia'],
# }


# print("=" * 70)
# print("MEDICAL RAG SYSTEM - SYMPTOMS & CAUSES ONLY")
# print("=" * 70)
# print("\nFeatures:")
# print("- BM25 + Vector Hybrid Search")
# print("- Cross-Encoder Reranking")
# print("- Medical Query Expansion")
# print("- Filters Out Diagnosis & Treatment Content")
# print("- Shows Only: Symptoms, Causes, Differential Diagnosis")


# # Load models
# print(f"\nLoading models...")
# device = "cuda" if torch.cuda.is_available() else "cpu"


# fast_model = SentenceTransformer(FAST_MODEL, device=device)
# if device == "cuda":
#     fast_model.half()
# print(f"[OK] Retrieval model loaded: {FAST_MODEL}")


# reranker = CrossEncoder(RERANK_MODEL, max_length=512, device=device)
# print(f"[OK] Reranker loaded: {RERANK_MODEL}")


# # Load BM25 index
# with open(BM25_INDEX_PATH, 'rb') as f:
#     bm25_data = pickle.load(f)
#     bm25 = bm25_data['bm25']
#     corpus = bm25_data['corpus']
#     chunks = bm25_data['chunks']
# print(f"[OK] BM25 index loaded: {len(corpus):,} documents")


# # Load ChromaDB
# chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
# collection = chroma_client.get_collection(name=COLLECTION_NAME)
# print(f"[OK] Vector DB loaded: {collection.count():,} chunks")


# def expand_query(query: str) -> str:
#     """Expand query with medical synonyms and conditions"""
#     query_lower = query.lower()
#     expanded_terms = [query]
    
#     # Add synonyms
#     for term, synonyms in MEDICAL_SYNONYMS.items():
#         if term in query_lower:
#             expanded_terms.extend(synonyms)
    
#     # Add related conditions
#     for symptom, conditions in SYMPTOM_CONDITIONS.items():
#         if symptom in query_lower:
#             expanded_terms.extend(conditions)
    
#     # Remove duplicates
#     unique_terms = list(dict.fromkeys(expanded_terms))
#     return ' '.join(unique_terms)


# def normalize_scores(scores: List[float]) -> List[float]:
#     """Normalize scores to [0, 1] range"""
#     if not scores or max(scores) == min(scores):
#         return [0.5] * len(scores)
#     min_score = min(scores)
#     max_score = max(scores)
#     return [(s - min_score) / (max_score - min_score) for s in scores]


# def filter_diagnosis_treatment_content(results: List[Dict]) -> List[Dict]:
#     """
#     Filter out diagnosis and treatment sections
#     Keep only: symptoms, causes, differential diagnosis, pathophysiology
#     """
    
#     # Keywords that indicate diagnosis/treatment content (to EXCLUDE)
#     exclude_keywords = [
#         # Diagnostic procedures
#         'diagnostic test', 'laboratory diagnosis', 'blood test', 'urine test',
#         'culture', 'biopsy', 'x-ray', 'ct scan', 'mri', 'ultrasound',
#         'ecg', 'ekg', 'serology', 'physical examination',
        
#         # Treatment terms
#         'treatment', 'management', 'drug of choice', 'medication',
#         'therapy', 'dose', 'dosage', 'mg/kg', 'orally', 'po divided',
#         'antibiotic', 'paracetamol', 'ibuprofen', 'analgesic',
#         'surgery', 'surgical', 'operation', 'procedure',
#         'prescription', 'administer', 'protocol',
        
#         # Treatment instructions
#         'take', 'drink fluids', 'rest until', 'apply',
#         'patient should', 'recommended dose', 'maximum dose',
#         'refer patient', 'hospitalization', 'admission',
#         'divided doses', 'per day', 'hourly', 'initial dose',
#     ]
    
#     # Keywords that indicate good content (to KEEP)
#     include_keywords = [
#         'causes of', 'cause', 'etiology', 'pathogenesis',
#         'symptoms', 'signs', 'clinical features', 'presentation',
#         'differential diagnosis', 'diagnosis include', 'may be due to',
#         'risk factors', 'associated with', 'commonly seen',
#         'characterized by', 'manifests as', 'typically presents',
#         'pathophysiology', 'mechanism', 'commonly occurs',
#     ]
    
#     filtered_results = []
    
#     for result in results:
#         text_lower = result['text'].lower()
#         text_preview = text_lower[:700]  # Check first 700 chars
        
#         # Count exclude keywords
#         exclude_count = sum(1 for keyword in exclude_keywords if keyword in text_preview)
        
#         # Count include keywords
#         include_count = sum(1 for keyword in include_keywords if keyword in text_preview)
        
#         # Decision logic
#         # If more exclude keywords than include keywords, skip it
#         if exclude_count > include_count + 2:  # Allow 2 keyword difference
#             continue
        
#         # If heavy treatment content, skip
#         treatment_heavy_keywords = [
#             'drug of choice', 'treatment', 'therapy', 'dosage', 'mg/kg',
#             'medication', 'dose', 'management', 'divided doses',
#             'maximum dose', 'initial dose'
#         ]
#         treatment_count = sum(1 for kw in treatment_heavy_keywords if kw in text_preview)
#         if treatment_count >= 3:  # If 3+ treatment keywords, skip
#             continue
        
#         # Strong exclude: if contains heavy dosage info
#         if 'mg/kg' in text_preview or 'po divided' in text_preview or 'hourly for' in text_preview:
#             continue
        
#         # Otherwise, keep it
#         filtered_results.append(result)
    
#     return filtered_results


# def hybrid_search(query: str) -> List[Dict]:
#     """Hybrid search with diagnosis/treatment filtering"""
    
#     start_time = time.time()
    
#     # Query expansion
#     expanded_query = expand_query(query)
#     if expanded_query != query:
#         print(f"\nExpanded query: {expanded_query[:150]}...")
    
#     # BM25 Search
#     bm25_start = time.time()
#     tokenized_query = word_tokenize(expanded_query.lower())
#     bm25_scores = bm25.get_scores(tokenized_query)
#     bm25_indices = np.argsort(bm25_scores)[::-1][:BM25_TOP_K]
    
#     bm25_results = {
#         idx: {
#             'text': corpus[idx],
#             'metadata': chunks[idx],
#             'bm25_score': float(bm25_scores[idx])
#         }
#         for idx in bm25_indices
#     }
#     bm25_time = (time.time() - bm25_start) * 1000
#     print(f"BM25: {len(bm25_results)} candidates ({bm25_time:.0f}ms)")
    
#     # Vector Search
#     vector_start = time.time()
#     vector_results = collection.query(
#         query_texts=[expanded_query],
#         n_results=VECTOR_TOP_K,
#         include=['documents', 'metadatas', 'distances']
#     )
    
#     vector_candidates = {}
#     for i in range(len(vector_results['documents'][0])):
#         text = vector_results['documents'][0][i]
#         try:
#             idx = corpus.index(text)
#             vector_candidates[idx] = {
#                 'text': text,
#                 'metadata': vector_results['metadatas'][0][i],
#                 'vector_score': 1 - vector_results['distances'][0][i]
#             }
#         except ValueError:
#             continue
    
#     vector_time = (time.time() - vector_start) * 1000
#     print(f"Vector: {len(vector_candidates)} candidates ({vector_time:.0f}ms)")
    
#     # Combine BM25 + Vector
#     all_indices = set(list(bm25_results.keys()) + list(vector_candidates.keys()))
    
#     bm25_scores_list = [bm25_results.get(idx, {'bm25_score': 0})['bm25_score'] for idx in all_indices]
#     vector_scores_list = [vector_candidates.get(idx, {'vector_score': 0})['vector_score'] for idx in all_indices]
    
#     norm_bm25 = normalize_scores(bm25_scores_list)
#     norm_vector = normalize_scores(vector_scores_list)
    
#     combined_candidates = []
#     for i, idx in enumerate(all_indices):
#         hybrid_score = (BM25_WEIGHT * norm_bm25[i]) + (VECTOR_WEIGHT * norm_vector[i])
        
#         combined_candidates.append({
#             'text': corpus[idx],
#             'metadata': chunks[idx],
#             'hybrid_score': hybrid_score,
#             'bm25_score': bm25_results.get(idx, {'bm25_score': 0})['bm25_score'],
#             'vector_score': vector_candidates.get(idx, {'vector_score': 0})['vector_score']
#         })
    
#     combined_candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)
#     combined_candidates = combined_candidates[:RERANK_TOP_K]
#     print(f"Hybrid: {len(combined_candidates)} combined candidates")
    
#     # Cross-Encoder Reranking
#     rerank_start = time.time()
#     pairs = [[query, candidate['text']] for candidate in combined_candidates]
#     rerank_scores = reranker.predict(pairs, show_progress_bar=False)
    
#     for i, candidate in enumerate(combined_candidates):
#         candidate['rerank_score'] = float(rerank_scores[i])
    
#     combined_candidates.sort(key=lambda x: x['rerank_score'], reverse=True)
    
#     # Normalize rerank scores
#     if combined_candidates:
#         min_rerank = min(c['rerank_score'] for c in combined_candidates)
#         max_rerank = max(c['rerank_score'] for c in combined_candidates)
        
#         if max_rerank != min_rerank:
#             for candidate in combined_candidates:
#                 candidate['rerank_score'] = (candidate['rerank_score'] - min_rerank) / (max_rerank - min_rerank)
#         else:
#             for candidate in combined_candidates:
#                 candidate['rerank_score'] = 0.5
    
#     rerank_time = (time.time() - rerank_start) * 1000
#     print(f"Rerank: {len(combined_candidates)} candidates ({rerank_time:.0f}ms)")
    
#     # Filter by score threshold
#     score_filtered = [c for c in combined_candidates if c['rerank_score'] > MIN_SCORE]
    
#     # Filter out diagnosis/treatment content
#     content_filtered = filter_diagnosis_treatment_content(score_filtered)
    
#     removed_count = len(score_filtered) - len(content_filtered)
#     if removed_count > 0:
#         print(f"[FILTER] Removed {removed_count} diagnosis/treatment sections")
    
#     # If too few results, relax filtering
#     if len(content_filtered) < 3 and len(score_filtered) >= 3:
#         print("[WARNING] Few results after filtering, showing top scored results...")
#         content_filtered = score_filtered[:FINAL_RESULTS]
    
#     total_time = (time.time() - start_time) * 1000
#     print(f"Total: {total_time:.0f}ms\n")
    
#     final_results = content_filtered[:FINAL_RESULTS]
#     return final_results


# print(f"\n{'=' * 70}")
# print("READY TO QUERY")
# print(f"{'=' * 70}\n")


# # Only run interactive query loop if script is executed directly
# # NOT when imported by FastAPI
# if __name__ == "__main__":
#     # Check if running as standalone script (not imported)
    
#     # If uvicorn is in the command, don't run interactive mode
#     if any('uvicorn' in arg.lower() for arg in sys.argv):
#         print("[INFO] Loaded as module - interactive mode disabled")
#     else:
#         # Interactive query loop (only when run directly: python step4_query_system_hybrid.py)
#         while True:
#             query = input("Query: ").strip()
            
#             if query.lower() in ['quit', 'exit', 'q']:
#                 print("\nGoodbye!")
#                 break
            
#             if not query:
#                 continue
            
#             try:
#                 results = hybrid_search(query)
                
#                 print(f"{'=' * 70}")
#                 print(f"RESULTS: {query}")
#                 print(f"{'=' * 70}")
                
#                 if not results:
#                     print("\n[ERROR] No results found.")
#                     print("\nTips:")
#                     print("- Try different medical terms")
#                     print("- Add more symptom-focused textbooks to books/ folder")
#                     print("- Check spelling")
#                 else:
#                     for i, result in enumerate(results, 1):
#                         print(f"\n[{i}] Relevance: {result['rerank_score']*100:.1f}%")
#                         print(f"    BM25: {result['bm25_score']:.2f} | Vector: {result['vector_score']*100:.1f}%")
#                         print(f"    Source: {result['metadata']['source']}")
#                         print(f"\n    {result['text'][:450]}...")
#                         print(f"{'-' * 70}")
                    
#                     print(f"\n[OK] Showing {len(results)} results (symptoms & causes only)")
                
#             except Exception as e:
#                 print(f"\n[ERROR] {str(e)}")
#                 import traceback
#                 traceback.print_exc()
        
#         print("\n" + "=" * 70 + "\n")
