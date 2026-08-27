def test_suggest_category_returns_none_with_no_history(client, auth_headers):
    response = client.post(
        "/transactions/suggest-category",
        json={"description": "Uber ride"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category_id"] is None
    assert body["category_name"] is None


def test_suggest_category_matches_from_past_transactions(client, auth_headers, categories):
    transport_id = categories["Transport"]["id"]
    # Teach it: past "Uber" transactions were categorized as Transport.
    for description in ["Uber ride home", "Uber to airport", "Uber eats"]:
        client.post(
            "/transactions/",
            json={
                "category_id": transport_id,
                "amount": "-15.00",
                "description": description,
                "transaction_date": "2026-01-01",
            },
            headers=auth_headers,
        )

    response = client.post(
        "/transactions/suggest-category",
        json={"description": "Uber trip downtown"},
        headers=auth_headers,
    )
    body = response.json()
    assert body["category_id"] == transport_id
    assert body["category_name"] == "Transport"


def test_suggest_category_picks_the_most_common_match(client, auth_headers, categories):
    food_id = categories["Food"]["id"]
    entertainment_id = categories["Entertainment"]["id"]
    # "Amazon" shows up under both categories, but Food wins 2-to-1.
    client.post("/transactions/", json={"category_id": food_id, "amount": "-20.00", "description": "Amazon groceries", "transaction_date": "2026-01-01"}, headers=auth_headers)
    client.post("/transactions/", json={"category_id": food_id, "amount": "-10.00", "description": "Amazon snacks", "transaction_date": "2026-01-02"}, headers=auth_headers)
    client.post("/transactions/", json={"category_id": entertainment_id, "amount": "-30.00", "description": "Amazon movie rental", "transaction_date": "2026-01-03"}, headers=auth_headers)

    response = client.post(
        "/transactions/suggest-category",
        json={"description": "Amazon order"},
        headers=auth_headers,
    )
    assert response.json()["category_id"] == food_id


def test_suggest_category_ignores_other_users_history(client, auth_headers, categories):
    client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    other_headers = {
        "Authorization": "Bearer "
        + client.post(
            "/auth/login", json={"email": "other@example.com", "password": "password123"}
        ).json()["access_token"]
    }
    other_categories = {c["name"]: c for c in client.get("/categories/", headers=other_headers).json()}
    client.post(
        "/transactions/",
        json={
            "category_id": other_categories["Transport"]["id"],
            "amount": "-15.00",
            "description": "Uber ride",
            "transaction_date": "2026-01-01",
        },
        headers=other_headers,
    )

    # The first user has no "Uber" history of their own, so nothing should match.
    response = client.post(
        "/transactions/suggest-category",
        json={"description": "Uber ride"},
        headers=auth_headers,
    )
    assert response.json()["category_id"] is None


def test_csv_import_blank_category_uses_suggestion(client, auth_headers, categories):
    food_id = categories["Food"]["id"]
    client.post(
        "/transactions/",
        json={"category_id": food_id, "amount": "-12.00", "description": "Starbucks coffee", "transaction_date": "2026-01-01"},
        headers=auth_headers,
    )

    csv_text = "date,description,category,amount\n2026-01-05,Starbucks latte,,-6.50\n"
    response = client.post(
        "/transactions/import",
        headers=auth_headers,
        files={"file": ("t.csv", csv_text.encode(), "text/csv")},
    )
    body = response.json()
    assert body["imported_count"] == 1

    transactions = client.get("/transactions/", params={"search": "latte"}, headers=auth_headers).json()
    assert transactions[0]["category_id"] == food_id


def test_csv_import_blank_category_with_no_match_fails_clearly(client, auth_headers):
    csv_text = "date,description,category,amount\n2026-01-05,Completely unknown thing,,-6.50\n"
    response = client.post(
        "/transactions/import",
        headers=auth_headers,
        files={"file": ("t.csv", csv_text.encode(), "text/csv")},
    )
    body = response.json()
    assert body["imported_count"] == 0
    assert "auto-suggest" in body["results"][0]["error"]
