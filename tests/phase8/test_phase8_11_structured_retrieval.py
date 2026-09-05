import pytest
from ai.retrieval.structured_retrieval_models import RetrievalSourceType
from ai.retrieval.structured_retrieval import StructuredRetrievalRouter
from ai.retrieval.standards_metadata_index import StandardsMetadataIndex
from ai.retrieval.product_standard_index import ProductStandardIndex

@pytest.fixture(scope="module")
def metadata_index():
    idx = StandardsMetadataIndex()
    # Inject IS 15750
    rec_15750 = {
        "standard_number": "IS 15750 : 2006",
        "internal_bis_id": "8074",
        "title": "Frost-free refrigerating appliances",
        "status": "Active",
        "source": {"source_url": "mock", "sha256": "mock", "retrieved_at": "mock"}
    }
    idx.records_by_id["8074"] = rec_15750
    idx.records_by_base.setdefault("15750", []).append(rec_15750)
    
    # Inject IS 60947 Part 2
    rec_60947_2 = {
        "standard_number": "IS/IEC 60947 : Part 2 : 2016",
        "internal_bis_id": "17914",
        "title": "Switchgear",
        "status": "Active"
    }
    idx.records_by_id["17914"] = rec_60947_2
    idx.records_by_base.setdefault("60947", []).append(rec_60947_2)

    # Inject IS 60947 Part 4 Section 1
    rec_60947_4_1 = {
        "standard_number": "IS/IEC 60947 : Part 4 : Sec 1",
        "internal_bis_id": "99999",
        "title": "Switchgear",
        "status": "Active"
    }
    idx.records_by_id["99999"] = rec_60947_4_1
    idx.records_by_base.setdefault("60947", []).append(rec_60947_4_1)

    return idx

@pytest.fixture(scope="module")
def product_index():
    idx = ProductStandardIndex()
    # Inject Refrigerator relationship
    idx.records.append({
        "relationship_id": "mock_refrig",
        "product_name": "Household refrigerators",
        "standard_number": "IS 15750:2006",
        "reconciliation_status": "MATCHED",
        "source": {"source_url": "mock", "sha256": "mock", "retrieved_at": "mock"},
        "table_index": 1,
        "row_index": 1
    })
    # Inject Ambiguous relationship
    idx.records.append({
        "relationship_id": "mock_ambig",
        "product_name": "Ambiguous product",
        "standard_number": "IS 12345",
        "reconciliation_status": "AMBIGUOUS_MATCH"
    })
    # Inject Year Mismatch
    idx.records.append({
        "relationship_id": "mock_year",
        "product_name": "Year mismatch product",
        "standard_number": "IS 12345:2012",
        "reconciliation_status": "YEAR_MISMATCH"
    })
    return idx

@pytest.fixture(scope="module")
def router(metadata_index, product_index):
    r = StructuredRetrievalRouter(metadata_index, product_index)
    r.rel_to_internal_id["mock_refrig"] = "8074"
    return r

def test_exact_standard_number_lookup(router):
    res = router.route_query("What is IS 15750?")
    assert len(res) > 0
    assert res[0].source_type == RetrievalSourceType.STANDARD_METADATA
    assert "15750" in res[0].standard_number
    assert res[0].metadata["internal_bis_id"] == "8074"

def test_base_number_lookup_no_part(router):
    # Base number with no part should not guess a part
    res = router.route_query("What is IS 60947?")
    assert len(res) > 0
    # The family has many records, should return AMBIGUOUS / multiple
    # and they should all be STANDARD_METADATA
    for r in res:
        assert r.source_type == RetrievalSourceType.STANDARD_METADATA
        assert "60947" in r.standard_number

def test_part_matching(router):
    res = router.route_query("What is IS 60947 Part 2?")
    assert len(res) > 0
    assert "part 2" in res[0].standard_number.lower()

def test_section_matching(router):
    res = router.route_query("What is IS 60947 Part 4 Section 1?")
    assert len(res) > 0
    std = res[0].standard_number.lower()
    assert "part 4" in std
    assert "sec 1" in std

def test_product_to_standard_refrigerator(router):
    # 14. Refrigerator query
    res = router.route_query("What is the Indian Standard for household refrigerators?")
    # Should find the product-to-standard relationship
    prod_res = [r for r in res if r.source_type == RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP]
    assert len(prod_res) > 0
    found = False
    for r in prod_res:
        if "refrigerator" in r.title.lower():
            assert "15750" in r.standard_number
            assert r.metadata.get("internal_bis_id") == "8074"
            found = True
            break
    assert found

def test_clause_query_routing(router):
    res = router.route_query("What does clause 6.2 require?")
    assert len(res) == 1
    assert res[0].source_type == RetrievalSourceType.DOCUMENT_EVIDENCE
    assert res[0].record_id == "ROUTING_SIGNAL"

def test_lifecycle_lookup(router):
    res = router.route_query("Is IS 15750 current?")
    assert len(res) > 0
    assert res[0].source_type == RetrievalSourceType.STANDARD_METADATA
    assert "status" in res[0].metadata

def test_ambiguous_relationship_preservation(router):
    # Test that the product index preserves unresolved relationships
    # Let's find one that is ambiguous
    for r in router.product_index.records:
        if r.get("reconciliation_status") == "AMBIGUOUS_MATCH":
            res = router.route_query(r["product_name"])
            prod_res = [x for x in res if x.source_type == RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP]
            assert prod_res[0].metadata["reconciliation_status"] == "AMBIGUOUS_MATCH"
            # And it MUST NOT have an internal BIS ID mapped
            assert "internal_bis_id" not in prod_res[0].metadata
            break

def test_year_mismatch_preservation(router):
    for r in router.product_index.records:
        if r.get("reconciliation_status") == "YEAR_MISMATCH":
            res = router.route_query(r["product_name"])
            prod_res = [x for x in res if x.source_type == RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP]
            assert prod_res[0].metadata["reconciliation_status"] == "YEAR_MISMATCH"
            assert "internal_bis_id" not in prod_res[0].metadata
            break

def test_provenance_completeness(router):
    res = router.route_query("What is IS 15750?")
    assert len(res) > 0
    prov = res[0].provenance
    assert "source_url" in prov
    assert "sha256" in prov
    
    prod_res = router.route_query("What is the Indian Standard for household refrigerators?")
    # Check product provenance
    for r in prod_res:
        if r.source_type == RetrievalSourceType.PRODUCT_STANDARD_RELATIONSHIP:
            prov = r.provenance
            assert "relationship_id" in prov
            assert "table_index" in prov
            assert "row_index" in prov

def test_duplicate_metadata_prevented(router):
    # A base number query should not return duplicate identical internal BIS IDs
    res = router.route_query("IS 15750")
    meta_ids = [r.metadata["internal_bis_id"] for r in res if r.source_type == RetrievalSourceType.STANDARD_METADATA]
    assert len(meta_ids) == len(set(meta_ids))

def test_title_lexical_lookup(router):
    res = router.route_query("frost free refrigerating appliances")
    found = False
    for r in res:
        if r.source_type == RetrievalSourceType.STANDARD_METADATA:
            if "frost-free refrigerating appliances" in r.title.lower() or "frost free" in r.title.lower():
                found = True
                break
    assert found
