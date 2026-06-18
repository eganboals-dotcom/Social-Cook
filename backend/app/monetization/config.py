"""Monetization configuration — the single source of truth for the freemium
model. Keep the "25 recipes per $10" numbers HERE so they are trivial to change.

Cap progression: 25 (free) -> 50 -> 75 -> 100 ... (+cap_increment per unlock).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapConfig:
    free_cap: int = 25  # recipes a user can save for free
    cap_increment: int = 25  # recipes unlocked per purchase
    unlock_price_usd: int = 10  # display price; the real price is set in the stores
    # RevenueCat / store product id for the consumable "+25 recipes" unlock.
    unlock_product_id: str = "recipe_unlock_25"


CAP_CONFIG = CapConfig()


def cap_after_unlocks(num_unlocks: int) -> int:
    """Total saved-recipe cap after a given number of successful unlocks."""
    return CAP_CONFIG.free_cap + num_unlocks * CAP_CONFIG.cap_increment
