def test_expense_transaction_requires_negative_amount(client, auth_headers, categories):
    response = client.post(
        "/transactions/",
        json={
            "category_id": categories["Food"]["id"],
            "amount": "10.00",  # positive amount on an expense category
            "transaction_date": "2026-01-15",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "negative" in response.json()["detail"]


def test_income_transaction_requires_positive_amount(client, auth_headers, categories):
    response = client.post(
        "/transactions/",
        json={
            "category_id": categories["Salary"]["id"],
            "amount": "-10.00",  # negative amount on an income category
            "transaction_date": "2026-01-15",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "positive" in response.json()["detail"]


def test_create_transaction_with_unowned_category_returns_404(client, auth_headers):
    response = client.post(
        "/transactions/",
        json={"category_id": 999999, "amount": "-5.00", "transaction_date": "2026-01-15"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_create_and_list_transaction(client, auth_headers, categories):
    create = client.post(
        "/transactions/",
        json={
            "category_id": categories["Food"]["id"],
            "amount": "-25.50",
            "description": "Groceries",
            "transaction_date": "2026-01-15",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201
    assert create.json()["amount"] == "-25.50"

    listed = client.get("/transactions/", headers=auth_headers).json()
    assert len(listed) == 1
    assert listed[0]["description"] == "Groceries"


def test_list_transactions_filters_by_search(client, auth_headers, categories):
    food_id = categories["Food"]["id"]
    client.post(
        "/transactions/",
        json={"category_id": food_id, "amount": "-10.00", "description": "Coffee shop", "transaction_date": "2026-01-01"},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"category_id": food_id, "amount": "-20.00", "description": "Groceries", "transaction_date": "2026-01-02"},
        headers=auth_headers,
    )

    response = client.get("/transactions/", params={"search": "coffee"}, headers=auth_headers)
    results = response.json()
    assert len(results) == 1
    assert results[0]["description"] == "Coffee shop"


def test_list_transactions_respects_pagination(client, auth_headers, categories):
    food_id = categories["Food"]["id"]
    for day in range(1, 6):
        client.post(
            "/transactions/",
            json={"category_id": food_id, "amount": "-1.00", "transaction_date": f"2026-01-0{day}"},
            headers=auth_headers,
        )

    page = client.get("/transactions/", params={"skip": 0, "limit": 2}, headers=auth_headers).json()
    assert len(page) == 2


def test_update_transaction(client, auth_headers, categories):
    created = client.post(
        "/transactions/",
        json={"category_id": categories["Food"]["id"], "amount": "-10.00", "transaction_date": "2026-01-15"},
        headers=auth_headers,
    ).json()

    response = client.put(
        f"/transactions/{created['id']}",
        json={"description": "Updated description"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_delete_transaction(client, auth_headers, categories):
    created = client.post(
        "/transactions/",
        json={"category_id": categories["Food"]["id"], "amount": "-10.00", "transaction_date": "2026-01-15"},
        headers=auth_headers,
    ).json()

    assert client.delete(f"/transactions/{created['id']}", headers=auth_headers).status_code == 204
    assert client.get("/transactions/", headers=auth_headers).json() == []


def test_transactions_are_scoped_per_user(client, auth_headers, categories):
    created = client.post(
        "/transactions/",
        json={"category_id": categories["Food"]["id"], "amount": "-10.00", "transaction_date": "2026-01-15"},
        headers=auth_headers,
    ).json()

    client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    other_headers = {
        "Authorization": "Bearer "
        + client.post(
            "/auth/login", json={"email": "other@example.com", "password": "password123"}
        ).json()["access_token"]
    }

    assert client.get("/transactions/", headers=other_headers).json() == []
    assert client.delete(f"/transactions/{created['id']}", headers=other_headers).status_code == 404
