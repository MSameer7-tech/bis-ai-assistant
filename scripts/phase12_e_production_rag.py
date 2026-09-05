import os
import sys
import json

# Ensure absolute paths if needed, or rely on execution context
from data.derived.phase12.grounded_rag_v1.answer_engine import GroundedRAGEngine
from scripts.phase12_b_hybrid_retrieval import RetrievalData
from sentence_transformers import SentenceTransformer

def get_production_engine(model_path="data/models/embeddings/all-MiniLM-L6-v2", device="cpu"):
    """
    Initializes and returns the Phase 12.E Production Grounded RAG Engine.
    Dynamically injects the Phase 12.DB verified optimal configuration
    without modifying the immutable retrieval_config.json baseline.
    """
    rdata = RetrievalData()
    
    # Load the base config from the frozen baseline
    base_config_path = "data/derived/phase12/hybrid_retrieval_v1/retrieval_config.json"
    with open(base_config_path, "r") as f:
        base_config = json.load(f)
        
    # Overlay the production configuration
    base_config["fusion"]["rrf_k"] = 20
    base_config["exact_match_boost"]["boost_factor"] = 2.5
    base_config["structured_retrieval"]["top_k"] = 10
    
    # By assigning to rdata.config, we bypass the internal json loading if implemented properly,
    # or override the loaded configuration.
    rdata.config = base_config
    
    # Initialize the embedding model
    model = SentenceTransformer(model_path, device=device)
    
    # Instantiate and return the Production Engine
    engine = GroundedRAGEngine(rdata, model)
    return engine

if __name__ == "__main__":
    engine = get_production_engine()
    print("Production Engine Initialized Successfully!")
    print(f"Injected Config: {engine.retrieval_data.config}")
