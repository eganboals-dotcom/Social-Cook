"""Lazily-constructed, cached SDK clients for the extraction providers.

Clients are created on first use and reused (they hold connection pools). A
missing API key raises ExtractionConfigError with a clear message rather than a
cryptic SDK error deep inside a request.
"""
from __future__ import annotations

from functools import lru_cache

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import get_settings
from app.extraction.errors import ExtractionConfigError


@lru_cache
def anthropic_client() -> AsyncAnthropic:
    key = get_settings().anthropic_api_key
    if not key:
        raise ExtractionConfigError(
            "ANTHROPIC_API_KEY is not set — add it to backend/.env"
        )
    return AsyncAnthropic(api_key=key)


@lru_cache
def openai_client() -> AsyncOpenAI:
    key = get_settings().openai_api_key
    if not key:
        raise ExtractionConfigError(
            "OPENAI_API_KEY is not set — add it to backend/.env"
        )
    return AsyncOpenAI(api_key=key)
