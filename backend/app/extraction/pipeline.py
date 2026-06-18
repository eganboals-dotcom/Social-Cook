"""Recipe extraction pipeline.

Order of operations (cheapest, highest-value signal first):
  1. Caption / description text   — always try first.
  2. Spoken audio (Transcriber)   — best-effort; only if media is available.
  3. On-screen text (VisionReader) — optional; only if frames are available.

Then: combine the available signals into one prompt -> LLM -> structured JSON ->
validate against `RecipeExtraction` before returning. Never trust raw model JSON.

Providers are injectable so the pipeline is easy to test and to extend.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.extraction.base import Transcriber, VideoIngest, VisionReader
from app.extraction.errors import NoRecipeFoundError
from app.extraction.llm import structure_recipe
from app.extraction.providers import (
    AnthropicVisionReader,
    ShareSheetIngest,
    WhisperTranscriber,
)
from app.schemas.recipe import RecipeExtraction


@dataclass
class ExtractionOutcome:
    recipe: RecipeExtraction
    platform: str | None
    raw_extraction: dict


async def extract_recipe(
    url: str,
    *,
    caption: str | None = None,
    use_audio: bool = False,
    use_vision: bool = False,
    ingest: VideoIngest | None = None,
    transcriber: Transcriber | None = None,
    vision: VisionReader | None = None,
) -> ExtractionOutcome:
    """Run the extraction pipeline and return a validated recipe + raw signals.

    `use_audio` / `use_vision` gate the optional, more expensive signals; they
    only do work if the ingest provider actually supplies media.
    """
    ingest = ingest or ShareSheetIngest()
    result = await ingest.ingest(url, caption=caption)

    caption_text = (result.caption or "").strip()

    transcript = ""
    if use_audio and result.audio_path:
        transcriber = transcriber or WhisperTranscriber()
        transcript = (await transcriber.transcribe(result.audio_path)).strip()

    vision_text = ""
    if use_vision and result.frame_paths:
        vision = vision or AnthropicVisionReader()
        vision_text = (await vision.read_frames(result.frame_paths)).strip()

    if not (caption_text or transcript or vision_text):
        raise NoRecipeFoundError(
            "No caption, audio, or on-screen text was available to read a recipe from."
        )

    recipe = await structure_recipe(
        caption=caption_text or None,
        transcript=transcript or None,
        vision_text=vision_text or None,
        platform=result.platform,
        url=url,
    )

    raw_extraction = {
        "caption": caption_text or None,
        "transcript": transcript or None,
        "vision_text": vision_text or None,
        "signals_used": [
            name
            for name, value in (
                ("caption", caption_text),
                ("audio", transcript),
                ("vision", vision_text),
            )
            if value
        ],
    }
    return ExtractionOutcome(
        recipe=recipe, platform=result.platform, raw_extraction=raw_extraction
    )
