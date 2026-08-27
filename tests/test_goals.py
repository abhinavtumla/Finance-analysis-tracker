def test_create_goal_response_includes_is_completed(client, auth_headers):
    # Regression test: GoalResponse.is_completed was briefly renamed to a
    # typo'd is_completad, which broke every goals endpoint with a
    # response-validation 500 because the router still built the dict with
    # the key "is_completed".
    response = client.post(
        "/goals/",
        json={"name": "Emergency Fund", "target_amount": "1000.00"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert "is_completed" in body
    assert body["is_completed"] is False
    assert body["progress_percentage"] == 0.0


def test_contribute_increases_current_amount_and_progress(client, auth_headers):
    goal = client.post(
        "/goals/",
        json={"name": "Vacation", "target_amount": "200.00"},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/goals/{goal['id']}/contribute",
        json={"amount": "50.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["current_amount"] == "50.00"
    assert body["progress_percentage"] == 25.0
    assert body["is_completed"] is False


def test_contribute_marks_goal_completed_at_target(client, auth_headers):
    goal = client.post(
        "/goals/",
        json={"name": "New Laptop", "target_amount": "100.00"},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/goals/{goal['id']}/contribute",
        json={"amount": "100.00"},
        headers=auth_headers,
    )
    body = response.json()
    assert body["is_completed"] is True
    assert body["progress_percentage"] == 100.0


def test_contribute_rejects_non_positive_amount(client, auth_headers):
    goal = client.post(
        "/goals/",
        json={"name": "Rainy Day", "target_amount": "100.00"},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/goals/{goal['id']}/contribute",
        json={"amount": "0.00"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_update_goal_name_and_target(client, auth_headers):
    goal = client.post(
        "/goals/",
        json={"name": "Old Name", "target_amount": "100.00"},
        headers=auth_headers,
    ).json()

    response = client.put(
        f"/goals/{goal['id']}",
        json={"name": "New Name", "target_amount": "200.00"},
        headers=auth_headers,
    )
    body = response.json()
    assert body["name"] == "New Name"
    assert body["target_amount"] == "200.00"


def test_delete_goal(client, auth_headers):
    goal = client.post(
        "/goals/",
        json={"name": "Disposable Goal", "target_amount": "100.00"},
        headers=auth_headers,
    ).json()

    assert client.delete(f"/goals/{goal['id']}", headers=auth_headers).status_code == 204
    assert client.get("/goals/", headers=auth_headers).json() == []
