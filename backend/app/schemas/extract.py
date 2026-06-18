"""Request/response contracts for the extraction endpoint."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.recipe import RecipeExtraction


class ExtractRequest(BaseModel):
    url: str
    caption: str | None = None
    # Optional, more-expensive signals. They only do work if a VideoIngest
    # provider can supply media (best-effort; the default share-sheet path can't).
    use_audio: bool = False
    use_vision: bool = False

    @field_validator("url")
    @classmethod
    def _url_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url must not be blank")
        return v


class ExtractResponse(BaseModel):
    recipe: RecipeExtraction
    source_platform: str | None = None
    # The signals used to build the recipe, kept for debugging / raw_extraction.
    raw_extraction: dict = Field(default_factory=dict)
