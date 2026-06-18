"""Recipe ORM model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Recipe(Base):
    __tablename__ = "recipes"
    # Non-unique index speeds up the soft duplicate check (per-user same URL).
    # Deliberately NOT a unique constraint — re-extraction is sometimes wanted.
    __table_args__ = (Index("ix_recipes_user_source", "user_id", "source_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(String(2048))
    source_platform: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    servings: Mapped[str | None] = mapped_column(String(64))
    # [{name, amount, unit}] and [{order, text}] — portable JSON (JSON on Postgres).
    ingredients: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # The caption/transcript/etc. used to build the recipe, for debugging.
    raw_extraction: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="recipes")
