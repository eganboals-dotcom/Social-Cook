"""RevenueCat integration: webhook auth, REST subscriber lookup, and parsing.

RevenueCat validates store receipts with Apple/Google on our behalf. Our job is
to trust RevenueCat — verified via the webhook shared secret or an authenticated
REST call — and never the client directly.
"""
from __future__ import annotations

import hmac
from dataclasses import dataclass

import httpx

from app.config import get_settings

REVENUECAT_API_BASE = "https://api.revenuecat.com/v1"

# RevenueCat event types that grant a consumable unlock.
CREDIT_EVENT_TYPES = {"NON_RENEWING_PURCHASE"}


class RevenueCatError(Exception):
    """RevenueCat REST call failed or is misconfigured."""


@dataclass(frozen=True)
class PurchaseTx:
    transaction_id: str
    product_id: str
    platform: str


@dataclass(frozen=True)
class WebhookEvent:
    type: str
    app_user_id: str | None
    product_id: str | None
    transaction_id: str | None
    platform: str


def _platform_from_store(store: str | None) -> str:
    s = (store or "").upper()
    if s in {"APP_STORE", "MAC_APP_STORE"}:
        return "apple"
    if s == "PLAY_STORE":
        return "google"
    return (store or "unknown").lower()


def verify_webhook_auth(authorization: str | None) -> bool:
    """Constant-time check of the RevenueCat webhook Authorization header."""
    secret = get_settings().revenuecat_webhook_auth
    if not secret or not authorization:
        return False
    return hmac.compare_digest(authorization, secret)


def parse_webhook_event(body: dict) -> WebhookEvent | None:
    event = body.get("event") if isinstance(body, dict) else None
    if not isinstance(event, dict):
        return None
    app_user_id = event.get("app_user_id")
    product_id = event.get("product_id")
    # transaction_id is the store transaction id (matches REST store_transaction_id).
    transaction_id = event.get("transaction_id") or event.get("id")
    return WebhookEvent(
        type=str(event.get("type") or ""),
        app_user_id=str(app_user_id) if app_user_id is not None else None,
        product_id=str(product_id) if product_id is not None else None,
        transaction_id=str(transaction_id) if transaction_id else None,
        platform=_platform_from_store(event.get("store")),
    )


def parse_non_subscriptions(
    subscriber_json: dict, *, product_id: str | None = None
) -> list[PurchaseTx]:
    """Pull consumable (non-subscription) transactions from a RevenueCat subscriber."""
    subscriber = (subscriber_json or {}).get("subscriber") or {}
    non_subs = subscriber.get("non_subscriptions") or {}
    out: list[PurchaseTx] = []
    for prod, txs in non_subs.items():
        if product_id is not None and prod != product_id:
            continue
        for tx in txs or []:
            txid = tx.get("store_transaction_id") or tx.get("id")
            if not txid:
                continue
            out.append(
                PurchaseTx(
                    transaction_id=str(txid),
                    product_id=str(prod),
                    platform=_platform_from_store(tx.get("store")),
                )
            )
    return out


class RevenueCatClient:
    """Minimal RevenueCat REST client (subscriber lookup for validation/restore)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else get_settings().revenuecat_api_key

    def get_subscriber(self, app_user_id: str) -> dict:
        if not self.api_key:
            raise RevenueCatError("REVENUECAT_API_KEY is not set")
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{REVENUECAT_API_BASE}/subscribers/{app_user_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
        except httpx.HTTPError as exc:
            raise RevenueCatError(f"RevenueCat request failed: {exc}") from exc
        if resp.status_code != 200:
            raise RevenueCatError(f"RevenueCat returned HTTP {resp.status_code}")
        return resp.json()
