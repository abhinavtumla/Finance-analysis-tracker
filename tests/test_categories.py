def test_create_category(client, auth_headers):
    response = client.post(
        "/categories/",
        json={"name": "Subscriptions", "type": "expense"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Subscriptions"
    assert body["is_default"] is False  # user-created categories are never marked default


def test_update_category(client, auth_headers, categories):
    food_id = categories["Food"]["id"]
    response = client.put(
        f"/categories/{food_id}",
        json={"name": "Groceries"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Groceries"


def test_delete_category(client, auth_headers, categories):
    entertainment_id = categories["Entertainment"]["id"]
    response = client.delete(f"/categories/{entertainment_id}", headers=auth_headers)
    assert response.status_code == 204

    remaining_names = {c["name"] for c in client.get("/categories/", headers=auth_headers).json()}
    assert "Entertainment" not in remaining_names


def test_categories_are_scoped_per_user(client, auth_headers, categories):
    client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    other_headers = {
        "Authorization": "Bearer "
        + client.post(
            "/auth/login", json={"email": "other@example.com", "password": "password123"}
        ).json()["access_token"]
    }

    food_id = categories["Food"]["id"]  # belongs to the first user, not "other"

    assert client.put(
        f"/categories/{food_id}", json={"name": "Hijacked"}, headers=other_headers
    ).status_code == 404
    assert client.delete(f"/categories/{food_id}", headers=other_headers).status_code == 404
