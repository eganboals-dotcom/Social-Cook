from __future__ import annotations

from app.config import get_settings
from app.monetization.revenuecat import (
    parse_non_subscriptions,
    parse_webhook_event,
    verify_webhook_auth,
)

WEBHOOK_SECRET = "test-webhook-secret"


def _signup(client, email="buyer@c.com"):
    resp = client.post("/auth/signup", json={"email": email, "password": "password123"})
    data = resp.json()
    return data["user"]["id"], {"Authorization": f"Bearer {data['access_token']}"}


def _webhook_body(user_id: int, transaction_id: str, product_id="recipe_unlock_25"):
    return {
        "event": {
            "type": "NON_RENEWING_PURCHASE",
            "app_user_id": str(user_id),
            "product_id": product_id,
            "transaction_id": transaction_id,
            "store": "APP_STORE",
        }
    }


# --- pure parsing / auth helpers (no DB) ---


def test_verify_webhook_auth(monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_auth", WEBHOOK_SECRET)
    assert verify_webhook_auth(WEBHOOK_SECRET) is True
    assert verify_webhook_auth("nope") is False
    assert verify_webhook_auth(None) is False


def test_verify_webhook_auth_no_secret_configured(monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_auth", None)
    # Secure default: reject everything when no secret is set.
    assert verify_webhook_auth("anything") is False


def test_parse_webhook_event():
    event = parse_webhook_event(_webhook_body(7, "txn_1"))
    assert event is not None
    assert event.type == "NON_RENEWING_PURCHASE"
    assert event.app_user_id == "7"
    assert event.product_id == "recipe_unlock_25"
    assert event.transaction_id == "txn_1"
    assert event.platform == "apple"
    assert parse_webhook_event({}) is None


def test_parse_non_subscriptions():
    subscriber = {
        "subscriber": {
            "non_subscriptions": {
                "recipe_unlock_25": [
                    {"store_transaction_id": "txn_A", "store": "APP_STORE"},
                    {"store_transaction_id": "txn_B", "store": "PLAY_STORE"},
                ],
                "some_other_product": [{"store_transaction_id": "txn_X", "store": "APP_STORE"}],
            }
        }
    }
    txs = parse_non_subscriptions(subscriber, product_id="recipe_unlock_25")
    assert [t.transaction_id for t in txs] == ["txn_A", "txn_B"]
    assert [t.platform for t in txs] == ["apple", "google"]


# --- config ---


def test_unlock_config(client):
    cfg = client.get("/purchases/config").json()
    assert cfg == {
        "free_cap": 25,
        "cap_increment": 25,
        "unlock_price_usd": 10,
        "product_id": "recipe_unlock_25",
    }


# --- webhook crediting ---


def test_webhook_requires_valid_secret(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_auth", WEBHOOK_SECRET)
    user_id, _ = _signup(client)
    resp = client.post(
        "/purchases/webhook",
        json=_webhook_body(user_id, "txn_1"),
        headers={"Authorization": "wrong"},
    )
    assert resp.status_code == 401


def test_webhook_credits_and_is_idempotent(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_auth", WEBHOOK_SECRET)
    user_id, auth = _signup(client)
    headers = {"Authorization": WEBHOOK_SECRET}

    first = client.post("/purchases/webhook", json=_webhook_body(user_id, "txn_1"), headers=headers)
    assert first.json()["status"] == "credited"
    assert client.get("/auth/me", headers=auth).json()["saved_recipe_cap"] == 50

    # Same transaction again -> no double credit.
    dup = client.post("/purchases/webhook", json=_webhook_body(user_id, "txn_1"), headers=headers)
    assert dup.json()["status"] == "duplicate"
    assert client.get("/auth/me", headers=auth).json()["saved_recipe_cap"] == 50

    # A new transaction -> another +25.
    second = client.post(
        "/purchases/webhook", json=_webhook_body(user_id, "txn_2"), headers=headers
    )
    assert second.json()["status"] == "credited"
    assert client.get("/auth/me", headers=auth).json()["saved_recipe_cap"] == 75


def test_webhook_ignores_other_products(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_auth", WEBHOOK_SECRET)
    user_id, auth = _signup(client)
    resp = client.post(
        "/purchases/webhook",
        json=_webhook_body(user_id, "txn_1", product_id="something_else"),
        headers={"Authorization": WEBHOOK_SECRET},
    )
    assert resp.json()["status"] == "ignored"
    assert client.get("/auth/me", headers=auth).json()["saved_recipe_cap"] == 25


# --- validate / restore (RevenueCat REST mocked) ---


def test_validate_reconciles_transactions(client, monkeypatch):
    _, auth = _signup(client)

    def fake_get_subscriber(self, app_user_id):
        return {
            "subscriber": {
                "non_subscriptions": {
                    "recipe_unlock_25": [
                        {"store_transaction_id": "txn_A", "store": "APP_STORE"},
                        {"store_transaction_id": "txn_B", "store": "PLAY_STORE"},
                    ]
                }
            }
        }

    monkeypatch.setattr(
        "app.monetization.revenuecat.RevenueCatClient.get_subscriber", fake_get_subscriber
    )

    first = client.post("/purchases/validate", headers=auth).json()
    assert first["credited"] == 2
    assert first["saved_recipe_cap"] == 75  # 25 + 2*25

    # Restore again -> nothing new.
    again = client.post("/purchases/validate", headers=auth).json()
    assert again["credited"] == 0
    assert again["saved_recipe_cap"] == 75

    history = client.get("/purchases", headers=auth).json()
    assert len(history["purchases"]) == 2


def test_validate_requires_auth(client):
    assert client.post("/purchases/validate").status_code == 401


def _recipe(title: str, source_url: str):
    return {
        "title": title,
        "servings": "1",
        "source_url": source_url,
        "source_platform": "tiktok",
        "ingredients": [{"name": "egg", "amount": "1", "unit": ""}],
        "steps": [{"order": 1, "text": "Cook."}],
    }


def test_credit_raises_cap_and_allows_more_saves(client, monkeypatch):
    """Integration: hitting the cap, then a purchase, lets the user save again."""
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_auth", WEBHOOK_SECRET)
    user_id, auth = _signup(client, "more@c.com")

    for i in range(25):  # fill the free cap
        resp = client.post("/recipes", json=_recipe(f"R{i}", f"u{i}"), headers=auth)
        assert resp.status_code == 201

    # 26th is blocked by the cap.
    assert client.post("/recipes", json=_recipe("R25", "u25"), headers=auth).status_code == 402

    # A validated purchase raises the cap by 25.
    credited = client.post(
        "/purchases/webhook",
        json=_webhook_body(user_id, "txn_more"),
        headers={"Authorization": WEBHOOK_SECRET},
    )
    assert credited.json()["status"] == "credited"

    # Now the same save succeeds.
    assert client.post("/recipes", json=_recipe("R25", "u25"), headers=auth).status_code == 201
