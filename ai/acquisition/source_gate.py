"""
Authoritative Source Verification and Acquisition Gate Module.
Enforces domain whitelisting, verification state transitions, and acquisition eligibility.
"""
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

AUTHORIZED_GOV_DOMAINS = {
    "bis.gov.in",
    "www.bis.gov.in",
    "egazette.gov.in",
    "www.egazette.gov.in",
    "manakonline.in",
    "www.manakonline.in",
    "crsbis.in",
    "www.crsbis.in",
    "standardsbis.bsbedge.com",
    "lims.bis.gov.in",
    "services.bis.gov.in",
    "www.services.bis.gov.in"
}

VALID_VERIFICATION_STATUSES = {
    "VERIFIED",
    "OFFLINE_RULES_VALID",
    "PENDING",
    "HTTP_ERROR",
    "NETWORK_FAILURE",
    "CONTENT_VALIDATION_FAILED",
    "TITLE_MISMATCH",
    "REDIRECT_OUTSIDE_AUTHORIZED_DOMAIN",
    "REJECTED_UNAUTHORIZED_DOMAIN",
    "SESSION_REQUIRED"
}


def is_domain_authorized(url: str) -> bool:
    """Verifies that a URL resolves to a whitelisted official government domain."""
    if not url:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return domain in AUTHORIZED_GOV_DOMAINS


def is_source_acquisition_eligible(source: Dict[str, Any], require_live_verified: bool = False) -> bool:
    """
    Authoritative acquisition gate function.
    Returns True if and only if:
    1. Source status is 'ACTIVE'.
    2. Canonical URL domain is authorized.
    3. Verification status is eligible (VERIFIED for live, or OFFLINE_RULES_VALID if live not required).
    4. Explicit acquisition_eligible flag is True.
    """
    if source.get("status") != "ACTIVE":
        return False

    canonical_url = source.get("canonical_url", "")
    if not is_domain_authorized(canonical_url):
        return False

    vmeta = source.get("verification_metadata")
    if not vmeta or not isinstance(vmeta, dict):
        return False

    status = vmeta.get("verification_status")
    if status not in VALID_VERIFICATION_STATUSES:
        return False

    # Check redirect safety
    final_url = vmeta.get("final_url")
    if final_url and not is_domain_authorized(final_url):
        return False

    if require_live_verified:
        return status == "VERIFIED" and vmeta.get("acquisition_eligible", False) is True
    else:
        return (status in {"VERIFIED", "OFFLINE_RULES_VALID"}) and vmeta.get("acquisition_eligible", False) is True
