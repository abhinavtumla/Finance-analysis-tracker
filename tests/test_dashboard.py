def test_dashboard_with_no_data_is_all_zero(client, auth_headers):
    response = client.get("/dashboard/", params={"month": 1, "year": 2026}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_balance"] == "0.00"
    assert body["monthly_income"] == "0.00"
    assert body["monthly_expenses"] == "0.00"
    assert body["monthly_budget"] is None


def test_dashboard_aggregates_income_and_expenses_for_the_month(client, auth_headers, categories):
    client.post(
        "/transactions/",
        json={"category_id": categories["Salary"]["id"], "amount": "2000.00", "transaction_date": "2026-02-01"},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"category_id": categories["Rent"]["id"], "amount": "-1200.00", "transaction_date": "2026-02-02"},
        headers=auth_headers,
    )
    # A transaction in a different month must not be counted.
    client.post(
        "/transactions/",
        json={"category_id": categories["Food"]["id"], "amount": "-30.00", "transaction_date": "2026-03-01"},
        headers=auth_headers,
    )

    response = client.get("/dashboard/", params={"month": 2, "year": 2026}, headers=auth_headers)
    body = response.json()
    assert body["monthly_income"] == "2000.00"
    assert body["monthly_expenses"] == "1200.00"
    assert body["total_balance"] == "770.00"  # all-time: 2000 - 1200 - 30


def test_dashboard_reflects_the_overall_budget(client, auth_headers, categories):
    client.post(
        "/budgets/",
        json={"category_id": None, "month": 9, "year": 2026, "limit_amount": "300.00"},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"category_id": categories["Food"]["id"], "amount": "-90.00", "transaction_date": "2026-09-05"},
        headers=auth_headers,
    )

    response = client.get("/dashboard/", params={"month": 9, "year": 2026}, headers=auth_headers)
    body = response.json()
    assert body["monthly_budget"] == "300.00"
    assert body["remaining_budget"] == "210.00"
    assert body["percentage_used"] == 30.0
    assert body["amount_exceeded"] == "0.00"


def test_dashboard_defaults_to_the_current_month_when_not_specified(client, auth_headers):
    response = client.get("/dashboard/", headers=auth_headers)
    assert response.status_code == 200  # just confirms month/year are optional
