"""Platform detection from a post URL.

ToS: we only read the URL's hostname to label the source platform — we do not
call any platform API or download media here.
"""
from __future__ import annotations

from urllib.parse import urlparse


def detect_platform(url: str | None) -> str | None:
    """Best-effort mapping of a URL to a known platform name, or None."""
    if not url:
        return None
    host = (urlparse(url).netloc or "").lower()
    host = host.removeprefix("www.")
    if "tiktok" in host:
        return "tiktok"
    if "instagram" in host:
        return "instagram"
    if "youtube" in host or "youtu.be" in host:
        return "youtube"
    return None
