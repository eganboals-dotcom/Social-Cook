"""Recipe endpoints — save, list/search, view, edit, delete, and bulk import.

Recipes belong to the authenticated user. The saved-recipe cap is enforced here
on every new save; the per-block numbers live in app/monetization/config.py.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe_io import (
    RecipeCreate,
    RecipeImportResult,
    RecipeListResponse,
    RecipeOut,
    RecipeSaveResponse,
    RecipeUpdate,
)
from app.services import count_user_recipes

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _find_by_source(db: Session, user_id: int, source_url: str | None) -> Recipe | None:
    if not source_url:
        return None
    return db.scalar(
        select(Recipe).where(Recipe.user_id == user_id, Recipe.source_url == source_url)
    )


def _cap_exceeded(user: User, count: int) -> HTTPException:
    # 402 Payment Required — the mobile client opens the paywall on this.
    return HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "message": (
                f"You've reached your saved-recipe limit "
                f"({count}/{user.saved_recipe_cap}). Unlock 25 more to keep saving."
            ),
            "saved_recipe_count": count,
            "saved_recipe_cap": user.saved_recipe_cap,
        },
    )


def _build_recipe(user_id: int, payload: RecipeCreate) -> Recipe:
    return Recipe(
        user_id=user_id,
        source_url=payload.source_url,
        source_platform=payload.source_platform,
        title=payload.title,
        servings=payload.servings,
        ingredients=[i.model_dump() for i in payload.ingredients],
        steps=[s.model_dump() for s in payload.steps],
        raw_extraction=payload.raw_extraction,
    )


@router.post("", response_model=RecipeSaveResponse)
def save_recipe(
    payload: RecipeCreate,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = _find_by_source(db, user.id, payload.source_url)
    if existing is not None:
        # Soft duplicate handling: return the existing recipe, don't re-save.
        response.status_code = status.HTTP_200_OK
        return RecipeSaveResponse(
            recipe=RecipeOut.model_validate(existing), already_saved=True
        )

    count = count_user_recipes(db, user.id)
    if count >= user.saved_recipe_cap:
        raise _cap_exceeded(user, count)

    recipe = _build_recipe(user.id, payload)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    response.status_code = status.HTTP_201_CREATED
    return RecipeSaveResponse(recipe=RecipeOut.model_validate(recipe), already_saved=False)


@router.get("", response_model=RecipeListResponse)
def list_recipes(
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Recipe).where(Recipe.user_id == user.id)
    if q:
        stmt = stmt.where(Recipe.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(Recipe.created_at.desc(), Recipe.id.desc())
    recipes = db.scalars(stmt).all()
    return RecipeListResponse(
        recipes=[RecipeOut.model_validate(r) for r in recipes],
        saved_recipe_count=count_user_recipes(db, user.id),
        saved_recipe_cap=user.saved_recipe_cap,
    )


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    return RecipeOut.model_validate(recipe)


@router.patch("/{recipe_id}", response_model=RecipeOut)
def update_recipe(
    recipe_id: int,
    payload: RecipeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    if payload.title is not None:
        recipe.title = payload.title
    if payload.servings is not None:
        recipe.servings = payload.servings
    if payload.ingredients is not None:
        recipe.ingredients = [i.model_dump() for i in payload.ingredients]
    if payload.steps is not None:
        recipe.steps = [s.model_dump() for s in payload.steps]
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return RecipeOut.model_validate(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found.")
    db.delete(recipe)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/import", response_model=RecipeImportResult)
def import_recipes(
    payload: list[RecipeCreate],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Local-first migration: bulk-import device recipes after signup.

    Skips duplicates (same source_url) and anything over the cap.
    """
    count = count_user_recipes(db, user.id)
    existing_urls = set(
        db.scalars(
            select(Recipe.source_url).where(
                Recipe.user_id == user.id, Recipe.source_url.is_not(None)
            )
        ).all()
    )

    imported = duplicates = skipped_over_cap = 0
    for item in payload:
        if item.source_url and item.source_url in existing_urls:
            duplicates += 1
            continue
        if count >= user.saved_recipe_cap:
            skipped_over_cap += 1
            continue
        db.add(_build_recipe(user.id, item))
        count += 1
        imported += 1
        if item.source_url:
            existing_urls.add(item.source_url)
    db.commit()

    return RecipeImportResult(
        imported=imported,
        duplicates=duplicates,
        skipped_over_cap=skipped_over_cap,
        saved_recipe_count=count_user_recipes(db, user.id),
        saved_recipe_cap=user.saved_recipe_cap,
    )
