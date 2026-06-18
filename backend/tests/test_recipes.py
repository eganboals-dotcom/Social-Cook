from __future__ import annotations


def _auth_headers(client, email="r@c.com"):
    resp = client.post(
        "/auth/signup", json={"email": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _recipe(title="Pasta", source_url="https://tiktok.com/v/1"):
    return {
        "title": title,
        "servings": "2",
        "source_url": source_url,
        "source_platform": "tiktok",
        "ingredients": [{"name": "spaghetti", "amount": "200", "unit": "g"}],
        "steps": [{"order": 1, "text": "Boil."}],
    }


def test_requires_auth(client):
    assert client.post("/recipes", json=_recipe()).status_code == 401
    assert client.get("/recipes").status_code == 401


def test_save_and_list(client):
    headers = _auth_headers(client)
    resp = client.post("/recipes", json=_recipe(), headers=headers)
    assert resp.status_code == 201
    assert resp.json()["already_saved"] is False
    recipe_id = resp.json()["recipe"]["id"]

    listing = client.get("/recipes", headers=headers).json()
    assert listing["saved_recipe_count"] == 1
    assert listing["saved_recipe_cap"] == 25
    assert listing["recipes"][0]["id"] == recipe_id
    assert listing["recipes"][0]["ingredients"][0]["unit"] == "g"


def test_duplicate_source_url_returns_existing(client):
    headers = _auth_headers(client)
    client.post("/recipes", json=_recipe(), headers=headers)
    second = client.post("/recipes", json=_recipe(title="Renamed"), headers=headers)
    assert second.status_code == 200
    assert second.json()["already_saved"] is True
    # Still only one saved.
    assert client.get("/recipes", headers=headers).json()["saved_recipe_count"] == 1


def test_search_by_title(client):
    headers = _auth_headers(client)
    client.post("/recipes", json=_recipe("Garlic Pasta", "u1"), headers=headers)
    client.post("/recipes", json=_recipe("Chocolate Cake", "u2"), headers=headers)
    found = client.get("/recipes", params={"q": "pasta"}, headers=headers).json()
    assert [r["title"] for r in found["recipes"]] == ["Garlic Pasta"]


def test_update_and_delete(client):
    headers = _auth_headers(client)
    recipe_id = client.post("/recipes", json=_recipe(), headers=headers).json()["recipe"]["id"]

    updated = client.patch(
        f"/recipes/{recipe_id}", json={"title": "New Title"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "New Title"

    assert client.delete(f"/recipes/{recipe_id}", headers=headers).status_code == 204
    assert client.get(f"/recipes/{recipe_id}", headers=headers).status_code == 404


def test_cap_is_enforced(client):
    headers = _auth_headers(client, "cap@c.com")
    for i in range(25):  # free cap is 25
        resp = client.post(
            "/recipes", json=_recipe(f"R{i}", f"https://t/{i}"), headers=headers
        )
        assert resp.status_code == 201
    over = client.post(
        "/recipes", json=_recipe("R25", "https://t/25"), headers=headers
    )
    assert over.status_code == 402
    detail = over.json()["detail"]
    assert detail["saved_recipe_count"] == 25
    assert detail["saved_recipe_cap"] == 25


def test_import_migration(client):
    headers = _auth_headers(client, "imp@c.com")
    # Pre-save one recipe so the import sees a duplicate.
    client.post("/recipes", json=_recipe("Existing", "https://dup"), headers=headers)

    payload = [
        _recipe("New1", "https://n1"),
        _recipe("Dup", "https://dup"),  # duplicate of the pre-saved one
        _recipe("New2", None),  # no source_url -> always imported
    ]
    resp = client.post("/recipes/import", json=payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["imported"] == 2
    assert body["duplicates"] == 1
    assert body["skipped_over_cap"] == 0
    assert body["saved_recipe_count"] == 3


def test_cannot_access_other_users_recipe(client):
    owner = _auth_headers(client, "owner@c.com")
    recipe_id = client.post("/recipes", json=_recipe(), headers=owner).json()["recipe"]["id"]

    other = _auth_headers(client, "other@c.com")
    assert client.get(f"/recipes/{recipe_id}", headers=other).status_code == 404
    patched = client.patch(f"/recipes/{recipe_id}", json={"title": "hax"}, headers=other)
    assert patched.status_code == 404
    assert client.delete(f"/recipes/{recipe_id}", headers=other).status_code == 404
    # Owner's recipe is untouched.
    assert client.get(f"/recipes/{recipe_id}", headers=owner).status_code == 200
