"""Shared slowapi limiter for rate-limiting auth endpoints.

Default storage is in-memory (fine for a single process / dev). Point
`storage_uri` at Redis for multi-process deployments.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
