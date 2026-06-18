"""Small data-access helpers shared by the API routers."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.auth import UserOut


def count_user_recipes(db: Session, user_id: int) -> int:
    """Saved-recipe count is derived from the recipes table (no drift)."""
    return (
        db.scalar(select(func.count()).select_from(Recipe).where(Recipe.user_id == user_id))
        or 0
    )


def to_user_out(db: Session, user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        saved_recipe_cap=user.saved_recipe_cap,
        saved_recipe_count=count_user_recipes(db, user.id),
        created_at=user.created_at,
    )
