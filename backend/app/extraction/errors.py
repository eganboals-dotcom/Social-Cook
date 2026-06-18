"""Extraction error types.

These map to friendly HTTP responses at the API layer — a video with no usable
recipe content should produce a clear message, not a crash.
"""
from __future__ import annotations


class ExtractionError(Exception):
    """Base class for recoverable extraction failures."""


class NoRecipeFoundError(ExtractionError):
    """The content didn't contain a usable recipe (expected, friendly case)."""


class ExtractionConfigError(ExtractionError):
    """A required API key or configuration value is missing."""
