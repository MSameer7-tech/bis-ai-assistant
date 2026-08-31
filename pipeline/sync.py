"""
BIS Knowledge Sync Command (Step 16).
Usage:
    python -m pipeline.sync
    python -m pipeline.sync --force
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.chunking.chunk_diff import ChunkDiffEngine
from ai.ingestion.change_detector import ChangeDetector
from ai.ingestion.manifest import IngestionManifestManager
from ai.ingestion.update_pipeline import IncrementalUpdatePipeline
from ai.versioning.semantic_diff import SemanticDiffEngine
from ai.vectorstore.indexer import IncrementalIndexer

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
METADATA_DIR = ROOT_DIR / "data" / "metadata"
REGISTRY_PATH = METADATA_DIR / "source_registry.json"
CHUNKS_DIR = ROOT_DIR / "data" / "chunks"


class KnowledgeSyncEngine:
    """Synchronizes knowledge repository with source records, incremental updates, and vector index."""

    def __init__(self):
        self.change_detector = ChangeDetector()
        self.update_pipeline = IncrementalUpdatePipeline()
        self.manifest_manager = IngestionManifestManager()
        self.semantic_diff = SemanticDiffEngine()
        self.chunk_diff = ChunkDiffEngine()
        self.indexer = IncrementalIndexer()

    def sync(self, force: bool = False) -> Dict[str, Any]:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)

        sources_checked = len(registry)
        unchanged_docs = []
        updated_docs = []
        new_docs = []
        failed_downloads = 0

        # Scan all documents
        for item in registry:
            doc_id = item.get("document_id")
            if not doc_id:
                continue

            local_path = ROOT_DIR / item.get("local_path", "")
            if not local_path.exists():
                failed_downloads += 1
                continue

            report = self.change_detector.check_document_change(doc_id, current_file_path=local_path, update_history=False)
            if report.get("has_changed"):
                updated_docs.append((doc_id, local_path))
            else:
                unchanged_docs.append(doc_id)

        docs_requiring_processing = list(updated_docs)
        if force and not docs_requiring_processing:
            first_item = registry[0]
            docs_requiring_processing.append((first_item["document_id"], ROOT_DIR / first_item["local_path"]))

        # Cumulative Metrics
        reqs_mod = 0
        reqs_add = 0
        reqs_rem = 0
        defs_mod = 0

        # Process any changed documents
        for doc_id, p_path in docs_requiring_processing:
            res = self.update_pipeline.process_updated_document(
                document_id=doc_id,
                new_pdf_path=p_path,
                force=True,
            )

            sem = res.get("semantic_diff", {})
            r_diff = sem.get("requirements_diff", {})
            reqs_mod += r_diff.get("modified_count", 0)
            reqs_add += r_diff.get("added_count", 0)
            reqs_rem += r_diff.get("removed_count", 0)
            defs_mod += sem.get("definitions_diff", {}).get("modified_count", 0)

        # Execute Incremental Vector Indexing (Step 16)
        index_metrics = self.indexer.index_chunks()

        # Update manifest
        self.manifest_manager.generate_manifest()

        return {
            "sources_checked": sources_checked,
            "unchanged_count": len(unchanged_docs),
            "new_count": len(new_docs),
            "updated_count": len(updated_docs),
            "failed_count": failed_downloads,
            "docs_processed": [d[0] for d in docs_requiring_processing],
            "semantic_changes": {
                "requirements_modified": reqs_mod,
                "requirements_added": reqs_add,
                "requirements_removed": reqs_rem,
                "definitions_modified": defs_mod,
            },
            "chunks": {
                "unchanged": index_metrics["unchanged_count"],
                "modified": index_metrics["modified_count"],
                "added": index_metrics["added_count"],
            },
            "embeddings": {
                "reused": index_metrics["embeddings_reused"],
                "generated": index_metrics["embeddings_generated"],
            },
            "vector_index_status": "Updated successfully",
        }


def run_sync(force: bool = False):
    engine = KnowledgeSyncEngine()
    result = engine.sync(force=force)

    print("\n" + "=" * 55)
    print("BIS Knowledge Sync")
    print("==================")
    print(f"Sources checked:       {result['sources_checked']:<6}")
    print(f"Unchanged:             {result['unchanged_count']:<6}")
    print(f"New documents:         {result['new_count']:<6}")
    print(f"Updated documents:     {result['updated_count']:<6}")
    print(f"Failed downloads:      {result['failed_count']:<6}")
    print("\nDocuments requiring processing:")
    if result["docs_processed"]:
        for doc_id in result["docs_processed"]:
            print(f"  {doc_id}")
    else:
        print("  (None - All sources up to date)")

    sem = result["semantic_changes"]
    print("\nSemantic changes:")
    print(f"  Requirements modified: {sem['requirements_modified']}")
    print(f"  Requirements added:    {sem['requirements_added']}")
    print(f"  Requirements removed:  {sem['requirements_removed']}")
    print(f"  Definitions modified:  {sem['definitions_modified']}")

    chk = result["chunks"]
    print("\nChunks:")
    print(f"  Unchanged:             {chk['unchanged']:,}")
    print(f"  Modified:              {chk['modified']}")
    print(f"  Added:                 {chk['added']}")

    emb = result["embeddings"]
    print("\nEmbeddings:")
    print(f"  Reused:                {emb['reused']:,}")
    print(f"  Generated:             {emb['generated']}")

    print("\nVector index:")
    print(f"  {result['vector_index_status']}")
    print("\nSync complete.")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize BIS knowledge repository and vector embeddings.")
    parser.add_argument("--force", action="store_true", help="Force sync pipeline execution")
    args = parser.parse_args()
    run_sync(force=args.force)
