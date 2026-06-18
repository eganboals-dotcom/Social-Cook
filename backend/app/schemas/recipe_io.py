"""Recipe save/list/import contracts for the API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.recipe import Ingredient, RecipeExtraction, Step


class RecipeCreate(RecipeExtraction):
    """A recipe to save — the validated recipe plus its source/debug fields."""

    source_url: str | None = None
    source_platform: str | None = None
    raw_extraction: dict | None = None


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_url: str | None = None
    source_platform: str | None = None
    title: str
    servings: str | None = None
    ingredients: list[Ingredient]
    steps: list[Step]
    created_at: datetime


class RecipeUpdate(BaseModel):
    """Partial edit of a saved recipe."""

    title: str | None = None
    servings: str | None = None
    ingredients: list[Ingredient] | None = None
    steps: list[Step] | None = None


class RecipeSaveResponse(BaseModel):
    recipe: RecipeOut
    # True when the user already had this source_url saved (we return the
    # existing recipe instead of creating a duplicate).
    already_saved: bool = False


class RecipeListResponse(BaseModel):
    recipes: list[RecipeOut]
    saved_recipe_count: int
    saved_recipe_cap: int


class RecipeImportResult(BaseModel):
    imported: int
    duplicates: int
    skipped_over_cap: int
    saved_recipe_count: int
    saved_recipe_cap: int
