def test_create_overall_budget(client, auth_headers):
    response = client.post(
        "/budgets/",
        json={"category_id": None, "month": 1, "year": 2026, "limit_amount": "500.00"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["spent"] == "0.00"
    assert body["remaining"] == "500.00"
    assert body["is_exceeded"] is False


def test_duplicate_overall_budget_rejected(client, auth_headers):
    # Regression test: category_id=NULL used to bypass the DB's unique
    # constraint because SQL treats every NULL as distinct from every other
    # NULL, so two "overall" budgets for the same month could both be
    # created. create_budget() now checks explicitly before inserting.
    payload = {"category_id": None, "month": 3, "year": 2026, "limit_amount": "200.00"}
    first = client.post("/budgets/", json=payload, headers=auth_headers)
    second = client.post("/budgets/", json=payload, headers=auth_headers)

    assert first.status_code == 201
    assert second.status_code == 400
    assert "already exists" in second.json()["detail"]


def test_duplicate_category_budget_rejected(client, auth_headers, categories):
    payload = {"category_id": categories["Food"]["id"], "month": 4, "year": 2026, "limit_amount": "100.00"}
    first = client.post("/budgets/", json=payload, headers=auth_headers)
    second = client.post("/budgets/", json=payload, headers=auth_headers)

    assert first.status_code == 201
    assert second.status_code == 400


def test_budget_spent_and_percentage_reflect_transactions(client, auth_headers, categories):
    food_id = categories["Food"]["id"]
    client.post(
        "/budgets/",
        json={"category_id": food_id, "month": 5, "year": 2026, "limit_amount": "100.00"},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"category_id": food_id, "amount": "-40.00", "transaction_date": "2026-05-10"},
        headers=auth_headers,
    )

    budgets = client.get("/budgets/", headers=auth_headers).json()
    budget = next(b for b in budgets if b["category_id"] == food_id)
    assert budget["spent"] == "40.00"
    assert budget["remaining"] == "60.00"
    assert budget["percentage_used"] == 40.0
    assert budget["is_exceeded"] is False


def test_budget_marks_exceeded_once_spending_passes_limit(client, auth_headers, categories):
    food_id = categories["Food"]["id"]
    client.post(
        "/budgets/",
        json={"category_id": food_id, "month": 6, "year": 2026, "limit_amount": "50.00"},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"category_id": food_id, "amount": "-75.00", "transaction_date": "2026-06-01"},
        headers=auth_headers,
    )

    budgets = client.get("/budgets/", headers=auth_headers).json()
    budget = next(b for b in budgets if b["category_id"] == food_id)
    assert budget["is_exceeded"] is True
    assert budget["remaining"] == "-25.00"


def test_update_budget_limit(client, auth_headers):
    created = client.post(
        "/budgets/",
        json={"category_id": None, "month": 7, "year": 2026, "limit_amount": "100.00"},
        headers=auth_headers,
    ).json()

    response = client.put(
        f"/budgets/{created['id']}",
        json={"limit_amount": "150.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["limit_amount"] == "150.00"


def test_delete_budget(client, auth_headers):
    created = client.post(
        "/budgets/",
        json={"category_id": None, "month": 8, "year": 2026, "limit_amount": "100.00"},
        headers=auth_headers,
    ).json()

    assert client.delete(f"/budgets/{created['id']}", headers=auth_headers).status_code == 204
    assert client.get("/budgets/", headers=auth_headers).json() == []
