"""Extraction tests that don't touch the network.

The single network seam (`llm._request_structured_recipe`) is monkeypatched, so
these exercise the real pipeline, signal-combining, and validation logic.
"""
from __future__ import annotations

import asyncio

import pytest

from app.extraction import llm, pipeline
from app.extraction.errors import NoRecipeFoundError
from app.extraction.platforms import detect_platform
from app.schemas.recipe import RecipeExtraction


def test_detect_platform():
    assert detect_platform("https://www.tiktok.com/@x/video/123") == "tiktok"
    assert detect_platform("https://instagram.com/reel/abc") == "instagram"
    assert detect_platform("https://www.youtube.com/shorts/x") == "youtube"
    assert detect_platform("https://youtu.be/x") == "youtube"
    assert detect_platform("https://example.com/x") is None
    assert detect_platform(None) is None


def test_to_recipe_found_maps_and_cleans():
    data = {
        "found": True,
        "title": "Garlic Pasta",
        "servings": "2",
        "ingredients": [
            {"name": "spaghetti", "amount": "200", "unit": "g"},
            {"name": "garlic", "amount": "3", "unit": ""},  # empty unit -> None
        ],
        "steps": [
            {"order": 5, "text": "Boil pasta."},  # order is renumbered to 1..N
            {"order": 9, "text": "Fry garlic."},
        ],
        "notes": "",
    }
    recipe = llm._to_recipe(data)
    assert isinstance(recipe, RecipeExtraction)
    assert recipe.title == "Garlic Pasta"
    assert recipe.servings == "2"
    assert recipe.ingredients[1].unit is None
    assert [s.order for s in recipe.steps] == [1, 2]


def test_to_recipe_not_found_raises():
    with pytest.raises(NoRecipeFoundError):
        llm._to_recipe(
            {
                "found": False,
                "title": "",
                "servings": "",
                "ingredients": [],
                "steps": [],
                "notes": "just a vibe, no recipe",
            }
        )


def test_to_recipe_found_but_empty_raises():
    with pytest.raises(NoRecipeFoundError):
        llm._to_recipe(
            {
                "found": True,
                "title": "",
                "servings": "",
                "ingredients": [],
                "steps": [],
                "notes": "",
            }
        )


def test_pipeline_no_signal_raises():
    with pytest.raises(NoRecipeFoundError):
        asyncio.run(pipeline.extract_recipe("https://tiktok.com/x", caption="   "))


def test_pipeline_with_caption(monkeypatch):
    async def fake_request(system: str, user: str) -> dict:
        # The caption text should have made it into the prompt.
        assert "2 eggs" in user
        return {
            "found": True,
            "title": "Test Dish",
            "servings": "4",
            "ingredients": [{"name": "egg", "amount": "2", "unit": ""}],
            "steps": [{"order": 1, "text": "Cook."}],
            "notes": "",
        }

    monkeypatch.setattr(llm, "_request_structured_recipe", fake_request)

    outcome = asyncio.run(
        pipeline.extract_recipe(
            "https://www.tiktok.com/@x/video/1", caption="2 eggs, cook"
        )
    )
    assert outcome.recipe.title == "Test Dish"
    assert outcome.platform == "tiktok"
    assert outcome.raw_extraction["signals_used"] == ["caption"]
    assert outcome.recipe.ingredients[0].amount == "2"
    assert outcome.recipe.ingredients[0].unit is None


def test_to_recipe_servings_blank_becomes_none():
    recipe = llm._to_recipe(
        {
            "found": True,
            "title": "X",
            "servings": "   ",
            "ingredients": [{"name": "egg", "amount": "1", "unit": ""}],
            "steps": [{"order": 1, "text": "Cook."}],
            "notes": "",
        }
    )
    assert recipe.servings is None


def test_to_recipe_blank_step_text_raises():
    with pytest.raises(NoRecipeFoundError):
        llm._to_recipe(
            {
                "found": True,
                "title": "X",
                "servings": "",
                "ingredients": [{"name": "egg", "amount": "1", "unit": ""}],
                "steps": [{"order": 1, "text": "   "}],
                "notes": "",
            }
        )
