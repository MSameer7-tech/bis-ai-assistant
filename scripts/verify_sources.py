#!/usr/bin/env python3
"""
Official Source Endpoint Verification Script for Phase 2B.
Performs health, domain, SSL/TLS, content-type, and title verification on registered BIS endpoints.
"""
import sys
import json
import argparse
import re
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone

try:
    import httpx
except ImportError:
    httpx = None

ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "data" / "sources" / "source_registry.json"
REPORT_PATH = ROOT_DIR / "data" / "sources" / "source_verification_report.json"

sys.path.insert(0, str(ROOT_DIR))
from ai.acquisition.source_gate import AUTHORIZED_GOV_DOMAINS, is_domain_authorized


def load_registry():
    if not REGISTRY_PATH.exists():
        print(f"Error: Missing {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(data):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def verify_endpoint_offline(source):
    """
    Offline validation of domain, schema, and pattern rules.
    Outputs the unified verification metadata schema.
    """
    url = source.get("canonical_url", "")
    domain_ok = is_domain_authorized(url)

    status = "OFFLINE_RULES_VALID" if domain_ok else "REJECTED_UNAUTHORIZED_DOMAIN"
    eligible = (status == "OFFLINE_RULES_VALID" and source.get("status") == "ACTIVE")

    return {
        "verification_status": status,
        "verification_mode": "OFFLINE",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "http_status": None,
        "final_url": url,
        "content_type": None,
        "content_type_valid": None,
        "title_match": None,
        "domain_whitelisted": domain_ok,
        "redirect_chain": [],
        "tls_verified": None,
        "acquisition_eligible": eligible
    }


def verify_endpoint_live(source, client):
    """
    Live HTTP verification of endpoint accessibility, TLS, content-type, redirects, and title.
    Outputs the unified verification metadata schema.
    """
    url = source.get("canonical_url", "")

    if not is_domain_authorized(url):
        return {
            "verification_status": "REJECTED_UNAUTHORIZED_DOMAIN",
            "verification_mode": "LIVE",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "http_status": None,
            "final_url": url,
            "content_type": None,
            "content_type_valid": False,
            "title_match": False,
            "domain_whitelisted": False,
            "redirect_chain": [],
            "tls_verified": False,
            "acquisition_eligible": False
        }

    try:
        response = client.get(url, timeout=12.0, follow_redirects=True)
        final_url = str(response.url)
        content_type = response.headers.get("content-type", "")

        # Trace redirect chain
        redirect_chain = [str(r.url) for r in response.history]

        # Gate: Check if final redirect domain is authorized
        if not is_domain_authorized(final_url):
            return {
                "verification_status": "REDIRECT_OUTSIDE_AUTHORIZED_DOMAIN",
                "verification_mode": "LIVE",
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "http_status": response.status_code,
                "final_url": final_url,
                "content_type": content_type,
                "content_type_valid": False,
                "title_match": False,
                "domain_whitelisted": False,
                "redirect_chain": redirect_chain,
                "tls_verified": True,
                "acquisition_eligible": False
            }

        # Gate: HTTP status check
        if not (200 <= response.status_code < 400):
            return {
                "verification_status": "HTTP_ERROR",
                "verification_mode": "LIVE",
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "http_status": response.status_code,
                "final_url": final_url,
                "content_type": content_type,
                "content_type_valid": False,
                "title_match": False,
                "domain_whitelisted": True,
                "redirect_chain": redirect_chain,
                "tls_verified": True,
                "acquisition_eligible": False
            }

        # Gate: Content type validation (HTML or PDF expected)
        ct_lower = content_type.lower()
        content_type_valid = ("text/html" in ct_lower or "application/pdf" in ct_lower or "application/json" in ct_lower)
        if not content_type_valid:
            return {
                "verification_status": "CONTENT_VALIDATION_FAILED",
                "verification_mode": "LIVE",
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "http_status": response.status_code,
                "final_url": final_url,
                "content_type": content_type,
                "content_type_valid": False,
                "title_match": False,
                "domain_whitelisted": True,
                "redirect_chain": redirect_chain,
                "tls_verified": True,
                "acquisition_eligible": False
            }

        # Gate: Title / pattern matching
        body_sample = response.text[:15000] if hasattr(response, "text") else ""
        pattern = source.get("expected_title_pattern")
        title_match = True
        if pattern:
            title_match = bool(re.search(pattern, body_sample, re.IGNORECASE))

        if not title_match:
            return {
                "verification_status": "TITLE_MISMATCH",
                "verification_mode": "LIVE",
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "http_status": response.status_code,
                "final_url": final_url,
                "content_type": content_type,
                "content_type_valid": True,
                "title_match": False,
                "domain_whitelisted": True,
                "redirect_chain": redirect_chain,
                "tls_verified": True,
                "acquisition_eligible": False
            }

        # All live validation gates passed
        return {
            "verification_status": "VERIFIED",
            "verification_mode": "LIVE",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "http_status": response.status_code,
            "final_url": final_url,
            "content_type": content_type,
            "content_type_valid": True,
            "title_match": True,
            "domain_whitelisted": True,
            "redirect_chain": redirect_chain,
            "tls_verified": True,
            "acquisition_eligible": True
        }

    except Exception as e:
        return {
            "verification_status": "NETWORK_FAILURE",
            "verification_mode": "LIVE",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "http_status": None,
            "final_url": url,
            "content_type": None,
            "content_type_valid": False,
            "title_match": False,
            "domain_whitelisted": True,
            "redirect_chain": [],
            "tls_verified": False,
            "error": str(e),
            "acquisition_eligible": False
        }


def main():
    parser = argparse.ArgumentParser(description="Verify BIS official source endpoints")
    parser.add_argument("--live", action="store_true", help="Perform live HTTP health checks with strict TLS")
    parser.add_argument("--update-registry", action="store_true", help="Update source_registry.json with results")
    args = parser.parse_args()

    registry_data = load_registry()
    sources = registry_data.get("sources", [])
    results = []

    print(f"🏛️ Verifying {len(sources)} official source endpoints (Live={args.live})...")

    if args.live and httpx:
        headers = {
            "User-Agent": "BIS-AI-Technical-Assistant-Acquisition/1.0 (Government-Regulatory-Research)"
        }
        # Strict TLS verification enabled
        with httpx.Client(headers=headers, verify=True, follow_redirects=True) as client:
            for s in sources:
                res = verify_endpoint_live(s, client)
                results.append(res)
                if args.update_registry:
                    s["verification_metadata"] = res
                print(f"  [{s['source_id']}] {s['source_name']}: {res['verification_status']} (Eligible={res['acquisition_eligible']})")
    else:
        for s in sources:
            res = verify_endpoint_offline(s)
            results.append(res)
            if args.update_registry:
                s["verification_metadata"] = res
            print(f"  [{s['source_id']}] {s['source_name']}: {res['verification_status']} (Mode=OFFLINE)")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_sources": len(sources),
        "verified_or_rule_valid_count": sum(1 for r in results if r["verification_status"] in {"VERIFIED", "OFFLINE_RULES_VALID"}),
        "rejected_or_error_count": sum(1 for r in results if r["verification_status"] not in {"VERIFIED", "OFFLINE_RULES_VALID"}),
        "results": results
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if args.update_registry:
        save_registry(registry_data)
        print(f"💾 Updated {REGISTRY_PATH}")

    print(f"📄 Verification report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
