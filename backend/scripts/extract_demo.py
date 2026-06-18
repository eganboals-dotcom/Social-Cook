"""Manual end-to-end test for the extraction pipeline (no UI required).

Usage (from the backend/ directory, with the venv active):
    python -m scripts.extract_demo
    python -m scripts.extract_demo --url <url> --caption "<caption text>"

Requires ANTHROPIC_API_KEY in the environment or backend/.env.
"""
from __future__ import annotations

import argparse
import asyncio

from app.extraction.errors import ExtractionConfigError, ExtractionError, NoRecipeFoundError
from app.extraction.pipeline import extract_recipe

SAMPLE_URL = "https://www.tiktok.com/@chef/video/1234567890"
SAMPLE_CAPTION = """\
15-Minute Garlic Butter Pasta — save this! Serves 2

Ingredients:
- 200g spaghetti
- 4 cloves garlic, minced
- 3 tbsp butter
- 1/4 cup parmesan, grated
- handful of parsley
- salt + pepper to taste

How to:
1. Boil the spaghetti in salted water until al dente; reserve 1/2 cup pasta water.
2. Melt butter in a pan, add garlic, and cook 1 minute until fragrant.
3. Add the drained pasta and a splash of pasta water; toss to coat.
4. Off the heat, stir in parmesan and parsley. Season and serve.
"""


async def _run(args: argparse.Namespace) -> None:
    try:
        outcome = await extract_recipe(
            args.url,
            caption=args.caption,
            use_audio=args.audio,
            use_vision=args.vision,
        )
    except NoRecipeFoundError as exc:
        print(f"\nNo recipe found: {exc}")
        return
    except ExtractionConfigError as exc:
        print(f"\nConfig error: {exc}")
        return
    except ExtractionError as exc:
        print(f"\nExtraction error: {exc}")
        return

    print("\n=== Extracted recipe ===")
    print(outcome.recipe.model_dump_json(indent=2))
    print(f"\nplatform: {outcome.platform}")
    print(f"signals used: {outcome.raw_extraction['signals_used']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a recipe from a URL + caption.")
    parser.add_argument("--url", default=SAMPLE_URL)
    parser.add_argument("--caption", default=SAMPLE_CAPTION)
    parser.add_argument("--audio", action="store_true", help="enable audio (no-op without media)")
    parser.add_argument("--vision", action="store_true", help="enable vision (needs frames)")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
