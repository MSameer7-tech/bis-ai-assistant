"""
Migration Script to Normalize Source URLs and Establish Authority Hierarchy (Step 3).
Normalizes Markdown-formatted links, strips brackets, separates source_url (provenance)
from official_url (authoritative BIS portal), and updates all metadata files.
"""

import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.acquisition.url_normalizer import normalize_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
METADATA_DIR = ROOT_DIR / "data" / "metadata"

OFFICIAL_PORTAL_MAP = {
    "SRC-001": "https://standardsbis.bsbedge.com",
    "SRC-002": "https://standardsbis.bsbedge.com",
    "SRC-003": "https://www.meity.gov.in/esdm/standards",
    "SRC-004": "https://www.bis.gov.in",
    "SRC-005": "https://www.crsbis.in",
    "SRC-006": "https://www.crsbis.in",
    "SRC-007": "https://standardsbis.bsbedge.com",
    "SRC-008": "https://www.lims.bis.gov.in",
    "SRC-009": "https://www.bis.gov.in/bis-apps/?lang=en",
    "SRC-010": "https://www.meity.gov.in/esdm/standards",
    "SRC-011": "https://www.meity.gov.in/esdm/standards",
    "SRC-012": "https://standardsbis.bsbedge.com",
}


def migrate_source_registry() -> Tuple[int, int]:
    """Migrates data/metadata/source_registry.json."""
    reg_path = METADATA_DIR / "source_registry.json"
    if not reg_path.exists():
        return 0, 0

    with open(reg_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    checked = 0
    changed = 0

    for rec in records:
        src_id = rec.get("source_id", "")
        # Raw url field
        if "url" in rec:
            checked += 1
            orig = rec["url"]
            cleaned = normalize_url(orig)
            if orig != cleaned:
                rec["url"] = cleaned
                changed += 1

        # source_url field
        if "source_url" in rec:
            checked += 1
            orig = rec["source_url"]
            cleaned = normalize_url(orig)
            if orig != cleaned:
                rec["source_url"] = cleaned
                changed += 1
        else:
            rec["source_url"] = rec.get("url", "")

        # official_url field
        if "official_url" not in rec or not rec["official_url"]:
            rec["official_url"] = OFFICIAL_PORTAL_MAP.get(src_id, "https://www.bis.gov.in")
            changed += 1

    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info("Migrated %s: %d checked, %d updated.", reg_path.name, checked, changed)
    return checked, changed


def migrate_all_metadata_files() -> Dict[str, Any]:
    """Scans all JSON files under data/metadata/ and normalizes any URL fields."""
    stats = {"files_migrated": 0, "urls_checked": 0, "urls_changed": 0}

    for json_file in METADATA_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                content = json.load(f)

            file_modified = False

            def walk_and_clean(obj: Any):
                nonlocal file_modified, stats
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(v, str) and ("url" in k.lower() or "http" in v):
                            stats["urls_checked"] += 1
                            cleaned = normalize_url(v)
                            if cleaned != v:
                                obj[k] = cleaned
                                stats["urls_changed"] += 1
                                file_modified = True
                        elif isinstance(v, (dict, list)):
                            walk_and_clean(v)
                elif isinstance(obj, list):
                    for item in obj:
                        walk_and_clean(item)

            walk_and_clean(content)

            if file_modified:
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                stats["files_migrated"] += 1

        except Exception as e:
            logger.warning("Could not process %s: %s", json_file.name, e)

    return stats


def main():
    print("\n" + "=" * 60)
    print("🔄 BIS SOURCE URL NORMALIZATION & MIGRATION")
    print("=" * 60)

    chk_reg, chg_reg = migrate_source_registry()
    all_stats = migrate_all_metadata_files()

    print(f"Registry Records Updated:    {chg_reg} fields")
    print(f"Total Metadata Files Scanned: {len(list(METADATA_DIR.glob('*.json')))}")
    print(f"Total URLs Checked:          {all_stats['urls_checked']}")
    print(f"Total URLs Cleaned:          {all_stats['urls_changed']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
