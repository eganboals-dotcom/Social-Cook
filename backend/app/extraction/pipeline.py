"""Recipe extraction pipeline — implemented in Phase 1.

Order of operations (cheapest, highest-value signal first):
  1. Caption / description text   — always try first.
  2. Spoken audio (Transcriber)   — best-effort.
  3. On-screen text (VisionReader) — optional; only when 1 + 2 are insufficient.

Then: combine the available signals into one prompt -> LLM -> structured JSON ->
validate against `RecipeExtraction` before returning. Never trust raw model JSON.
"""
from __future__ import annotations

from app.schemas.recipe import RecipeExtraction


async def extract_recipe(
    url: str,
    *,
    caption: str | None = None,
    use_audio: bool = False,
    use_vision: bool = False,
) -> RecipeExtraction:
    """Run the extraction pipeline and return a validated recipe.

    `use_audio` / `use_vision` gate the optional, more expensive signals.
    """
    raise NotImplementedError("extract_recipe — Phase 1")
