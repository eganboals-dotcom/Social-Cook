"""Recipe data contracts.

These pydantic models define the structured recipe shape the extraction pipeline
must produce. The LLM returns raw JSON; we validate it against `RecipeExtraction`
before anything is saved or returned — never trust raw model output.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Ingredient(BaseModel):
    name: str
    # Amounts are kept as strings on purpose: real recipes say "1/2", "a pinch",
    # "2-3", etc., which don't fit cleanly into a number.
    amount: str | None = None
    unit: str | None = None

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("ingredient name must not be blank")
        return v


class Step(BaseModel):
    order: int = Field(ge=1)
    text: str

    @field_validator("text")
    @classmethod
    def _text_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("step text must not be blank")
        return v


class RecipeExtraction(BaseModel):
    """A validated recipe produced by the extraction pipeline / LLM."""

    title: str
    servings: str | None = None
    ingredients: list[Ingredient] = Field(min_length=1)
    steps: list[Step] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v
