"""Monetization endpoints: unlock config, RevenueCat webhook, validate/restore, history.

The cap is only ever raised here, after server-side validation — the client is
never trusted to set it.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.purchase import Purchase
from app.models.user import User
from app.monetization.config import CAP_CONFIG
from app.monetization.revenuecat import (
    CREDIT_EVENT_TYPES,
    RevenueCatClient,
    RevenueCatError,
    parse_non_subscriptions,
    parse_webhook_event,
    verify_webhook_auth,
)
from app.monetization.service import credit_unlock, reconcile_transactions
from app.schemas.purchase import (
    PurchaseListResponse,
    PurchaseOut,
    UnlockConfig,
    ValidateResponse,
)
from app.services import count_user_recipes

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.get("/config", response_model=UnlockConfig)
def unlock_config():
    return UnlockConfig(
        free_cap=CAP_CONFIG.free_cap,
        cap_increment=CAP_CONFIG.cap_increment,
        unlock_price_usd=CAP_CONFIG.unlock_price_usd,
        product_id=CAP_CONFIG.unlock_product_id,
    )


@router.post("/webhook")
def revenuecat_webhook(
    payload: dict,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Authoritative crediting path. RevenueCat POSTs purchase events here with a
    shared-secret Authorization header that we verify."""
    if not verify_webhook_auth(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook authorization"
        )

    event = parse_webhook_event(payload)
    if (
        event is None
        or event.type not in CREDIT_EVENT_TYPES
        or event.product_id != CAP_CONFIG.unlock_product_id
    ):
        return {"status": "ignored"}
    if not event.app_user_id or not event.app_user_id.isdigit():
        return {"status": "unknown_user"}

    user = db.get(User, int(event.app_user_id))
    if user is None:
        return {"status": "unknown_user"}

    credited = credit_unlock(
        db,
        user,
        platform=event.platform,
        product_id=event.product_id,
        transaction_id=event.transaction_id or "",
    )
    return {"status": "credited" if credited else "duplicate"}


@router.post("/validate", response_model=ValidateResponse)
def validate_purchases(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Client-driven validation + restore: ask RevenueCat for this user's
    consumable transactions and credit any we haven't recorded yet."""
    try:
        subscriber = RevenueCatClient().get_subscriber(str(user.id))
    except RevenueCatError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not validate with RevenueCat: {exc}",
        ) from exc

    transactions = parse_non_subscriptions(subscriber, product_id=CAP_CONFIG.unlock_product_id)
    credited = reconcile_transactions(db, user, transactions)
    db.refresh(user)
    return ValidateResponse(
        credited=credited,
        saved_recipe_cap=user.saved_recipe_cap,
        saved_recipe_count=count_user_recipes(db, user.id),
    )


@router.get("", response_model=PurchaseListResponse)
def list_purchases(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Purchase)
        .where(Purchase.user_id == user.id)
        .order_by(Purchase.validated_at.desc(), Purchase.id.desc())
    ).all()
    return PurchaseListResponse(purchases=[PurchaseOut.model_validate(r) for r in rows])
