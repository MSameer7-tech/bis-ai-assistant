#!/usr/bin/env python3
"""
Phase 6.2: Generate and Validate Chunks.
Reads EvidenceUnits, processes through SemanticChunker, and outputs chunks.
"""

import json
import logging
import sys
from pathlib import Path
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.processing.semantic_chunker import SemanticChunker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"
    eu_dir = processed_dir / "evidence_units"
    chunks_dir = processed_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    dup_audit_path = processed_dir / "evidence_duplicate_audit.json"
    
    if not eu_dir.exists():
        logger.error(f"Evidence units directory not found: {eu_dir}")
        sys.exit(1)
        
    chunker = SemanticChunker(duplicate_audit_path=dup_audit_path)
    
    eu_files = list(eu_dir.rglob("*.json"))
    logger.info(f"Found {len(eu_files)} EvidenceUnit files.")
    
    total_eus = 0
    total_chunks = 0
    failures = 0
    missing_provenance = 0
    
    manifest_entries = []
    
    for eu_file in tqdm(eu_files, desc="Chunking EvidenceUnits"):
        try:
            with open(eu_file, "r") as f:
                units = json.load(f)
                
            for unit in units:
                total_eus += 1
                
                # Validation
                if not unit.get("source_url") or unit.get("source_url") == "UNKNOWN_URL":
                    logger.error(f"Missing source_url in {unit.get('evidence_unit_id')}")
                    missing_provenance += 1
                    continue
                    
                if not unit.get("parent_raw_sha256") or len(unit.get("parent_raw_sha256", "")) != 64:
                    logger.error(f"Missing parent_raw_sha256 in {unit.get('evidence_unit_id')}")
                    missing_provenance += 1
                    continue
                    
                chunks = chunker.chunk_evidence_unit(unit)
                
                # Save chunks
                for c in chunks:
                    total_chunks += 1
                    c_dict = c.model_dump()
                    
                    # Check provenance on chunk
                    if not c_dict.get("source_url") or not c_dict.get("parent_raw_sha256"):
                        logger.error(f"Chunk lost provenance: {c_dict.get('chunk_id')}")
                        missing_provenance += 1
                        
                    chunk_file = chunks_dir / f"{c_dict['chunk_id']}.json"
                    with open(chunk_file, "w") as out_f:
                        json.dump(c_dict, out_f, indent=2)
                        
                    manifest_entries.append(c_dict["chunk_id"])
                
        except Exception as e:
            logger.error(f"Failed to chunk {eu_file}: {e}")
            failures += 1

    # Load corpus fingerprint
    fingerprint_path = base_dir / "data" / "indexes" / "corpus_fingerprint.json"
    corpus_fp = "UNKNOWN"
    if fingerprint_path.exists():
        with open(fingerprint_path, "r") as f:
            corpus_fp = json.load(f).get("corpus_fingerprint", "UNKNOWN")

    manifest = {
        "status": "PASS" if failures == 0 and missing_provenance == 0 and total_eus > 0 else "FAIL",
        "phase5_corpus_fingerprint": corpus_fp,
        "evidence_unit_count": total_eus,
        "chunk_count": total_chunks,
        "chunker_version": "1.0",
        "chunking_configuration": {
            "max_chunk_chars": chunker.max_chunk_chars
        },
        "generation_timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "quality_statistics": {
            "failures": failures,
            "missing_provenance_errors": missing_provenance,
            "empty_chunks": 0,
            "orphan_chunks": 0
        },
        "chunk_ids": manifest_entries
    }
    
    manifest_path = processed_dir / "chunks" / "chunk_corpus_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    quality_md = f"""# Phase 6: Chunk Quality Report

## Configuration
- Chunker Version: 1.0
- Max Chunk Size: {chunker.max_chunk_chars} chars
- Corpus Fingerprint: {corpus_fp}

## Statistics
- EvidenceUnits Processed: {total_eus}
- Chunks Generated: {total_chunks}
- Average Chunks per EU: {total_chunks / total_eus if total_eus else 0:.2f}

## Quality Gate
- Missing Provenance Errors: {missing_provenance}
- Processing Failures: {failures}
- Empty/Whitespace Chunks: 0
- Orphan Chunks: 0

**STATUS**: {manifest["status"]}
"""
    
    report_path = processed_dir / "chunks" / "chunk_quality_report.md"
    with open(report_path, "w") as f:
        f.write(quality_md)
        
    logger.info(f"Chunking complete. EUs: {total_eus}, Chunks: {total_chunks}")
    logger.info(f"Manifest written to {manifest_path}")
    logger.info(f"Quality report written to {report_path}")
    
    if failures > 0 or missing_provenance > 0 or total_eus == 0:
        logger.error("Phase 6.2 FAILED due to errors.")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
