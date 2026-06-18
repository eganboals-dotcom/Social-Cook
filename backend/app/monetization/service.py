"""Cap-crediting logic — the single place that grants saved-recipe unlocks.

Idempotent on transaction_id (also enforced by a unique DB constraint), so the
same purchase never credits twice — whether it arrives via the RevenueCat
webhook or via client-driven validation / restore.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.purchase import Purchase
from app.models.user import User
from app.monetization.config import CAP_CONFIG
from app.monetization.revenuecat import PurchaseTx


def credit_unlock(
    db: Session,
    user: User,
    *,
    platform: str,
    product_id: str,
    transaction_id: str,
) -> bool:
    """Record a validated unlock and raise the user's cap. Returns False if the
    transaction was already credited (idempotent)."""
    if not transaction_id:
        return False
    if db.scalar(select(Purchase).where(Purchase.transaction_id == transaction_id)) is not None:
        return False

    user.saved_recipe_cap += CAP_CONFIG.cap_increment
    db.add(user)
    db.add(
        Purchase(
            user_id=user.id,
            platform=platform[:16],
            product_id=product_id,
            transaction_id=transaction_id,
            cap_added=CAP_CONFIG.cap_increment,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # Concurrent credit of the same transaction — unique constraint won.
        db.rollback()
        return False
    return True


def reconcile_transactions(db: Session, user: User, transactions: list[PurchaseTx]) -> int:
    """Credit any not-yet-recorded unlock transactions; returns how many were new."""
    credited = 0
    for tx in transactions:
        if tx.product_id != CAP_CONFIG.unlock_product_id:
            continue
        if credit_unlock(
            db,
            user,
            platform=tx.platform,
            product_id=tx.product_id,
            transaction_id=tx.transaction_id,
        ):
            credited += 1
    return credited
