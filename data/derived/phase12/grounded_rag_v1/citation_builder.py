def build_citations(evidence_list):
    """
    Build citation mappings from evidence.
    """
    citations = {}
    for i, e in enumerate(evidence_list, 1):
        cid = f"[{i}]"
        citations[cid] = {
            "source_record_id": e.source_record_id,
            "retrieval_unit_id": e.retrieval_unit_id,
            "source_url": e.source_url,
            "title": e.document_title or e.source_title or "",
            "authority": e.authority or "UNKNOWN",
            "provenance": {}
        }
    return citations
