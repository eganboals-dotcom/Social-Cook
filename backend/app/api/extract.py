"""Recipe extraction endpoint."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.extraction.errors import (
    ExtractionConfigError,
    ExtractionError,
    NoRecipeFoundError,
)
from app.extraction.pipeline import extract_recipe
from app.schemas.extract import ExtractRequest, ExtractResponse

router = APIRouter(tags=["extraction"])


@router.post("/extract", response_model=ExtractResponse)
async def extract(req: ExtractRequest) -> ExtractResponse:
    """Turn a URL + optional caption (and optional audio/vision) into a recipe."""
    try:
        outcome = await extract_recipe(
            req.url,
            caption=req.caption,
            use_audio=req.use_audio,
            use_vision=req.use_vision,
        )
    except NoRecipeFoundError as exc:
        # Expected, friendly case — not a server error.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ExtractionConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ExtractResponse(
        recipe=outcome.recipe,
        source_platform=outcome.platform,
        raw_extraction=outcome.raw_extraction,
    )
