import json
import pytest
from pathlib import Path
from ai.acquisition.discovery.query_driven import QueryDrivenStrategy
from ai.acquisition.discovery.api_interceptor import APIInterceptorStrategy

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_query_driven_no_hardcoded_mappings():
    """Verify no hardcoded mappings in the QueryDrivenStrategy source."""
    strategy_path = ROOT_DIR / "ai/acquisition/discovery/query_driven.py"
    content = strategy_path.read_text().lower()
    
    assert "refrigerator" not in content, "Hardcoded product mapping found"
    assert "15750" not in content, "Hardcoded IS number mapping found"

def test_api_interceptor_no_hardcoded_mappings():
    """Verify no hardcoded mappings in the APIInterceptorStrategy source."""
    strategy_path = ROOT_DIR / "ai/acquisition/discovery/api_interceptor.py"
    content = strategy_path.read_text().lower()
    
    assert "refrigerator" not in content, "Hardcoded product mapping found"
    assert "15750" not in content, "Hardcoded IS number mapping found"

def test_live_query_driven_refrigerator():
    strategy = QueryDrivenStrategy()
    
    # We will pass a specific subset of products for testing by patching load_query_vocabulary
    strategy.load_query_vocabulary = lambda: ["refrigerator", "water heater", "helmet"]
    
    source = {
        "source_id": "SRC-001",
        "canonical_url": "https://www.bis.gov.in/know-your-standard/",
        "source_family_id": "SRCF-001"
    }
    
    candidates, metrics = strategy.discover(source)
    
    relationships = metrics.dom_metrics.get("relationships", [])
    
    print(f"\nCandidates found: {len(candidates)}")
    print(f"Relationships found: {len(relationships)}")
    
    for r in relationships:
        print(f"Rel: {r['product_name']} -> IS {r['standard_number']} ({r['standard_title']})")
        
    for c in candidates:
        print(f"Cand: {c.candidate_id} - {c.title}")

    assert len(relationships) > 0

def test_live_api_interceptor():
    strategy = APIInterceptorStrategy(max_pages=2)
    source = {
        "source_id": "SRC-005",
        "canonical_url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/",
        "source_family_id": "SRCF-006"
    }
    
    candidates, metrics = strategy.discover(source)
    
    relationships = metrics.dom_metrics.get("relationships", [])
    total = metrics.dom_metrics.get("total_records_reported", 0)
    collected = metrics.dom_metrics.get("records_collected", 0)
    
    print(f"\nTotal Reported: {total}")
    print(f"Total Collected: {collected}")
    print(f"Pagination Complete: {metrics.dom_metrics.get('pagination_complete')}")
    
    assert collected > 0
