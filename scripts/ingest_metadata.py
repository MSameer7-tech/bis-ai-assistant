source_data = {
    "external_source_id": external_source_id,

    "name": name,

    "url": url,

    "source_type": (
        record.get("source_type")
        or "other"
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
