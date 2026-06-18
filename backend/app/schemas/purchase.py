"""Purchase / monetization API contracts."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UnlockConfig(BaseModel):
    """Surfaces the freemium numbers to the client (single source of truth)."""

    free_cap: int
    cap_increment: int
    unlock_price_usd: int
    product_id: str


class ValidateResponse(BaseModel):
    credited: int
    saved_recipe_cap: int
    saved_recipe_count: int


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    product_id: str
    transaction_id: str
    cap_added: int
    validated_at: datetime


class PurchaseListResponse(BaseModel):
    purchases: list[PurchaseOut]
