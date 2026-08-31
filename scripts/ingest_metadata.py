source_type_map = {
    "standard_document": "bis_standard",
    "qco_order": "qco",
    "scheme_regulation": "certification_document",
    "guideline": "guideline",
    "lab_directory": "laboratory",
}

source_data = {
    "external_source_id": external_source_id,

    "name": name,

    "url": url,

    "source_type": source_type_map.get(
        record.get("source_type"),
        "other"
    ),

    "authority_level": (
        record.get("authority_level")
        or "unknown"
    ),

    "description": record.get("notes"),

    "last_verified_at": normalize_datetime(
        record.get("retrieval_date")
    ),
}
