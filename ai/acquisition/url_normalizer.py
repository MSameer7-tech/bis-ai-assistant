"""
URL Normalization Utility for BIS Ingestion & Source Registry.
Strips Markdown links, brackets, and formatting artifacts to ensure canonical raw URLs.
"""

import re
from typing import Optional


def normalize_url(url: Optional[str]) -> str:
    """
    Normalizes a source URL string to a clean, raw HTTP/HTTPS URL.
    Converts:
        - Markdown links: '[https://archive.org/...](https://archive.org/...)' -> 'https://archive.org/...'
        - Named markdown: '[Archive Link](https://archive.org/...)' -> 'https://archive.org/...'
        - Bracketed URLs: '[https://archive.org/...]' -> 'https://archive.org/...'
        - Malformed markdown artifacts: 'https://archive.org/...](https://archive.org/...)' -> 'https://archive.org/...'
    """
    if not url:
        return ""

    url_str = str(url).strip()

    # 1. Full standard Markdown link: [text](http://...)
    full_md = re.fullmatch(r"\[([^\]]*)\]\((https?://[^\s\)]+)\)", url_str)
    if full_md:
        return full_md.group(2).strip()

    # 2. Bracketed raw URL: [http://...]
    bracketed = re.fullmatch(r"\[(https?://[^\s\]]+)\]", url_str)
    if bracketed:
        return bracketed.group(1).strip()

    # 3. Partial / truncated markdown artifact: ...](http://...) or (http://...)
    paren_match = re.search(r"\]\((https?://[^\s\)]+)\)", url_str)
    if paren_match:
        return paren_match.group(1).strip()

    paren_only = re.search(r"\((https?://[^\s\)]+)\)", url_str)
    if paren_only and url_str.startswith("["):
        return paren_only.group(1).strip()

    # 4. Strip surrounding quotes or stray brackets
    clean = url_str.strip("'\"<>[]()")
    return clean
