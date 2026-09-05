#!/usr/bin/env python3
"""
Step 6 & 7: Phase 6 BM25 & Vector Indexing.
Builds the exact Phase 6 indexes from the frozen SemanticChunk corpus.
"""
import json
import logging
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Use SentenceTransformers to match BAAI/bge-small-en-v1.5 locally or fallback
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    pass

import chromadb
from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase6Indexer")

CHUNKS_DIR = ROOT_DIR / "data" / "processed" / "chunks"
INDEXES_DIR = ROOT_DIR / "data" / "indexes"
INDEXES_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "BAAI/bge-small-en-v1.5"

def run_indexing():
    logger.info("🚀 Starting Phase 6 Indexing...")
    
    # 1. Load Fingerprints
    corpus_fp_path = INDEXES_DIR / "corpus_fingerprint.json"
    if not corpus_fp_path.exists():
        logger.error("Missing corpus_fingerprint.json")
        sys.exit(1)
    with open(corpus_fp_path, "r") as f:
        corpus_fp = json.load(f).get("corpus_fingerprint")

    chunk_manifest_path = CHUNKS_DIR / "chunk_corpus_manifest.json"
    if not chunk_manifest_path.exists():
        logger.error("Missing chunk_corpus_manifest.json")
        sys.exit(1)
    with open(chunk_manifest_path, "r") as f:
        chunk_manifest = json.load(f)
        
    chunker_version = chunk_manifest.get("chunker_version", "1.0")
    
    # Generate Chunk Corpus Fingerprint (hash of all sorted chunk IDs)
    chunk_ids = chunk_manifest.get("chunk_ids", [])
    chunk_ids.sort()
    chunk_corpus_fp = hashlib.sha256("".join(chunk_ids).encode('utf-8')).hexdigest()

    # 2. Load Chunks
    chunk_files = list(CHUNKS_DIR.glob("CH-*.json"))
    logger.info(f"Loading {len(chunk_files)} chunks...")
    
    chunks = []
    for cf in tqdm(chunk_files, desc="Loading Chunks"):
        with open(cf, "r") as f:
            c = json.load(f)
            chunks.append(c)
            
    # 3. Build BM25
    logger.info("Building BM25 Index...")
    tokenized_corpus = [c["chunk_text"].lower().split(" ") for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    
    bm25_manifest = {
        "status": "BUILT",
        "tokenizer": "whitespace_lower",
        "corpus_fingerprint": corpus_fp,
        "chunk_corpus_fingerprint": chunk_corpus_fp,
        "bm25_configuration": "Okapi",
        "chunk_count": len(chunks)
    }
    
    with open(INDEXES_DIR / "bm25_manifest.json", "w") as f:
        json.dump(bm25_manifest, f, indent=2)
        
    # 4. Build Vector Index (Chroma)
    logger.info("Building Vector Index (ChromaDB)...")
    
    chroma_path = INDEXES_DIR / "chroma_phase6"
    client = chromadb.PersistentClient(path=str(chroma_path))
    
    # We recreate the collection to ensure deterministic Phase 6 baseline
    collection_name = "bis_phase6_baseline"
    try:
        client.delete_collection(collection_name)
    except:
        pass
    collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    
    # Load model
    logger.info(f"Loading Embedding Model: {MODEL_NAME}")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to load model {MODEL_NAME}: {e}")
        logger.error("Please install sentence-transformers or ensure network access.")
        sys.exit(1)
        
    # Embed in batches
    BATCH_SIZE = 256
    failures = 0
    
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Embedding & Indexing"):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["chunk_text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        
        # Build metadata explicitly containing required provenance
        metadatas = []
        for c in batch:
            metadatas.append({
                "chunk_id": c["chunk_id"],
                "evidence_unit_id": c["evidence_unit_id"],
                "document_id": c["document_id"],
                "source_url": c["source_url"],
                "parent_raw_sha256": c["parent_raw_sha256"],
                "clause": str(c.get("clause") or ""),
                "section": str(c.get("section") or ""),
                "page": str(c.get("page") or ""),
                "document_type": c["document_type"],
                "source_family": c.get("source_family_id", "UNKNOWN"),
                "duplicate_group_id": str(c.get("duplicate_group_id") or "")
            })
            
        try:
            embeddings = model.encode(texts, normalize_embeddings=True).tolist()
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Embedding batch failed: {e}")
            failures += 1
            
    if failures > 0:
        logger.error(f"Vector indexing failed with {failures} batch errors.")
        sys.exit(1)
        
    vector_manifest = {
        "model_name": MODEL_NAME,
        "model_revision": "v1.5",
        "embedding_dimension": 384,
        "distance_metric": "cosine",
        "normalization_configuration": "L2_normalized",
        "corpus_fingerprint": corpus_fp,
        "chunk_corpus_fingerprint": chunk_corpus_fp,
        "chunker_version": chunker_version
    }
    
    with open(INDEXES_DIR / "vector_manifest.json", "w") as f:
        json.dump(vector_manifest, f, indent=2)
        
    # 5. Hybrid Manifest & Canonical Index Manifest
    hybrid_manifest = {
        "status": "BUILT",
        "rrf_configuration": {"k": 60, "dense_weight": 1.0, "sparse_weight": 1.0},
        "diversification_configuration": {"enabled": True, "max_per_doc": 3}
    }
    with open(INDEXES_DIR / "hybrid_manifest.json", "w") as f:
        json.dump(hybrid_manifest, f, indent=2)
        
    canonical_id_str = f"{corpus_fp}_{chunker_version}_{MODEL_NAME}_v1.5_384_cosine_Okapi_RRF60"
    canonical_version = hashlib.md5(canonical_id_str.encode('utf-8')).hexdigest()
    
    index_manifest = {
        "index_version": canonical_version,
        "corpus_fingerprint": corpus_fp,
        "chunk_corpus_fingerprint": chunk_corpus_fp,
        "evidence_unit_count": chunk_manifest.get("evidence_unit_count"),
        "chunk_count": len(chunks),
        "chunker_version": chunker_version,
        "embedding_model": MODEL_NAME,
        "embedding_revision": "v1.5",
        "embedding_dimension": 384,
        "distance_metric": "cosine",
        "bm25_configuration": "Okapi",
        "rrf_configuration": "k=60",
        "diversification_configuration": "group_aware",
        "chroma_collection": collection_name,
        "creation_timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    with open(INDEXES_DIR / "index_manifest.json", "w") as f:
        json.dump(index_manifest, f, indent=2)
        
    logger.info("✅ Phase 6 Indexing Complete.")

if __name__ == "__main__":
    run_indexing()
