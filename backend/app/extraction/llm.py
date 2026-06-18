"""LLM recipe structuring via the Anthropic API (claude-sonnet-4-6).

Takes the combined extraction signals (caption + optional transcript + optional
on-screen text) and asks Claude to return a structured recipe. We use structured
outputs (`output_config.format`) so the model returns JSON matching our schema,
then validate that JSON with pydantic before returning — raw model output is
never trusted.

Note: the structured-outputs JSON schema can't express constraints like
"min 1 item" or "integer >= 1", so the schema here is intentionally lenient and
the strict contract is enforced by `RecipeExtraction` in `_to_recipe`.
"""
from __future__ import annotations

import json

from pydantic import ValidationError

from app.config import get_settings
from app.extraction.clients import anthropic_client
from app.extraction.errors import ExtractionError, NoRecipeFoundError
from app.schemas.recipe import Ingredient, RecipeExtraction, Step

# Lenient schema handed to the model. Every field is required (structured outputs
# is strict), so "unknown" values come back as "" and are cleaned to None below.
_RECIPE_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "found": {
            "type": "boolean",
            "description": "True only if the signals contain a real, cookable recipe.",
        },
        "title": {"type": "string", "description": "Dish name, or '' if not found."},
        "servings": {"type": "string", "description": "Servings as stated, or ''."},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "amount": {"type": "string", "description": "e.g. '1/2', '200', or ''."},
                    "unit": {"type": "string", "description": "e.g. 'g', 'cup', or ''."},
                },
                "required": ["name", "amount", "unit"],
            },
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "order": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["order", "text"],
            },
        },
        "notes": {
            "type": "string",
            "description": "If found is false, a short reason why.",
        },
    },
    "required": ["found", "title", "servings", "ingredients", "steps", "notes"],
}

_SYSTEM_PROMPT = (
    "You are a precise recipe extraction engine for a cooking app. You receive "
    "text signals pulled from a social-media cooking video (the post caption, and "
    "optionally an audio transcript and on-screen text) and must extract a single "
    "structured recipe.\n\n"
    "Rules:\n"
    "- Use ONLY information present in the provided signals. Never invent "
    "ingredients, amounts, or steps that the text does not support.\n"
    "- If the signals do not actually describe a cookable recipe (e.g. it's just a "
    "promo or a vibe with no ingredients/steps), set \"found\" to false and give a "
    "short reason in \"notes\".\n"
    "- Prefer the caption for the ingredient list and amounts; use the transcript "
    "and on-screen text to fill gaps and confirm ordering.\n"
    "- Split each ingredient into name / amount / unit. Use \"\" for amount or unit "
    "when not stated.\n"
    "- Steps must be concise, imperative, and in cooking order.\n"
    "- Title is the dish name; servings as stated, else \"\"."
)


def _clean(value: object) -> str | None:
    """Strip a value to a non-empty string, or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _build_user_prompt(
    *,
    caption: str | None,
    transcript: str | None,
    vision_text: str | None,
    platform: str | None,
    url: str | None,
) -> str:
    parts: list[str] = [
        "Extract the recipe from the following cooking-video signals.",
        "",
    ]
    if url:
        parts.append(f"Source URL: {url}")
    if platform:
        parts.append(f"Platform: {platform}")
    parts.append("")
    if caption:
        parts += ["=== POST CAPTION (most reliable) ===", caption.strip(), ""]
    if transcript:
        parts += ["=== AUDIO TRANSCRIPT ===", transcript.strip(), ""]
    if vision_text:
        parts += ["=== ON-SCREEN TEXT ===", vision_text.strip(), ""]
    return "\n".join(parts).strip()


async def _request_structured_recipe(system: str, user: str) -> dict:
    """Call the LLM with structured output and return the parsed JSON dict.

    This is the only network seam in this module — tests monkeypatch it.
    """
    client = anthropic_client()
    settings = get_settings()
    resp = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": _RECIPE_JSON_SCHEMA}},
    )
    if getattr(resp, "stop_reason", None) == "refusal":
        raise NoRecipeFoundError(
            "The model declined to extract a recipe from this content."
        )
    text = next(
        (b.text for b in resp.content if getattr(b, "type", None) == "text"), None
    )
    if not text:
        raise ExtractionError("The model returned no text to parse.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ExtractionError("The model returned malformed JSON.") from exc
    if not isinstance(data, dict):
        raise ExtractionError("The model returned an unexpected JSON shape.")
    return data


def _to_recipe(data: dict) -> RecipeExtraction:
    """Map the lenient model JSON onto the strict, validated recipe contract."""
    if not data.get("found"):
        reason = _clean(data.get("notes")) or "We couldn't find a recipe in this post."
        raise NoRecipeFoundError(reason)
    try:
        ingredients = [
            Ingredient(
                name=str(item.get("name", "")),
                amount=_clean(item.get("amount")),
                unit=_clean(item.get("unit")),
            )
            for item in data.get("ingredients", [])
        ]
        # Renumber steps sequentially so order is always 1..N (avoids gaps/dupes).
        steps = [
            Step(order=index + 1, text=str(item.get("text", "")))
            for index, item in enumerate(data.get("steps", []))
        ]
        return RecipeExtraction(
            title=str(data.get("title", "")),
            servings=_clean(data.get("servings")),
            ingredients=ingredients,
            steps=steps,
        )
    except ValidationError as exc:
        # The model claimed a recipe, but it failed our contract (e.g. no
        # ingredients). Treat as "no usable recipe" rather than a 500.
        raise NoRecipeFoundError(
            "We couldn't read a complete recipe from this post."
        ) from exc


async def structure_recipe(
    *,
    caption: str | None = None,
    transcript: str | None = None,
    vision_text: str | None = None,
    platform: str | None = None,
    url: str | None = None,
) -> RecipeExtraction:
    """Combine the available signals into one prompt and return a validated recipe."""
    user = _build_user_prompt(
        caption=caption,
        transcript=transcript,
        vision_text=vision_text,
        platform=platform,
        url=url,
    )
    data = await _request_structured_recipe(_SYSTEM_PROMPT, user)
    return _to_recipe(data)
