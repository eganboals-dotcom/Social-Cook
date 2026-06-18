from __future__ import annotations


def _signup(client, email="a@b.com", password="password123"):
    return client.post("/auth/signup", json={"email": email, "password": password})


def test_signup_returns_token_and_user(client):
    resp = _signup(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "a@b.com"
    assert data["user"]["saved_recipe_cap"] == 25
    assert data["user"]["saved_recipe_count"] == 0


def test_me_with_token(client):
    token = _signup(client).json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "a@b.com"


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401
    assert (
        client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"}).status_code
        == 401
    )


def test_signup_duplicate_email_conflicts(client):
    _signup(client)
    assert _signup(client).status_code == 409


def test_signup_rejects_short_password(client):
    resp = client.post("/auth/signup", json={"email": "x@y.com", "password": "short"})
    assert resp.status_code == 422


def test_login_success_and_failure(client):
    _signup(client, "u@v.com", "password123")
    ok = client.post("/auth/login", json={"email": "u@v.com", "password": "password123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    bad = client.post("/auth/login", json={"email": "u@v.com", "password": "wrongpass1"})
    assert bad.status_code == 401

    missing = client.post(
        "/auth/login", json={"email": "no@one.com", "password": "password123"}
    )
    assert missing.status_code == 401


def test_forgot_password_unknown_email_is_generic(client):
    resp = client.post("/auth/forgot-password", json={"email": "ghost@nowhere.com"})
    assert resp.status_code == 200


def test_password_reset_flow(client, monkeypatch):
    _signup(client, "reset@me.com", "password123")

    captured: dict[str, str] = {}

    import app.email as email_mod

    class CaptureSender(email_mod.EmailSender):
        def send(self, *, to: str, subject: str, body: str) -> None:
            captured["body"] = body

    monkeypatch.setattr("app.api.auth.get_email_sender", lambda: CaptureSender())

    resp = client.post("/auth/forgot-password", json={"email": "reset@me.com"})
    assert resp.status_code == 200

    token = captured["body"].split("token=", 1)[1].split()[0]
    reset = client.post(
        "/auth/reset-password", json={"token": token, "new_password": "newpassword456"}
    )
    assert reset.status_code == 200

    # Old password no longer works; new one does.
    assert (
        client.post(
            "/auth/login", json={"email": "reset@me.com", "password": "password123"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login", json={"email": "reset@me.com", "password": "newpassword456"}
        ).status_code
        == 200
    )


def test_reset_with_bad_token_fails(client):
    resp = client.post(
        "/auth/reset-password", json={"token": "garbage", "new_password": "newpassword456"}
    )
    assert resp.status_code == 400
