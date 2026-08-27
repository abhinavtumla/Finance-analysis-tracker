def test_register_creates_user_and_seeds_default_categories(client):
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123", "full_name": "Alice"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["full_name"] == "Alice"
    assert body["is_active"] is True
    assert "hashed_password" not in body  # UserResponse must never leak the hash

    categories = client.get(
        "/categories/",
        headers=_login(client, "alice@example.com", "password123"),
    ).json()
    assert len(categories) == 6
    assert all(c["is_default"] for c in categories)


def test_register_duplicate_email_rejected(client):
    payload = {"email": "bob@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "carol@example.com", "password": "correct-password"})
    response = client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_unknown_email_rejected(client):
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert response.status_code == 401


def test_me_requires_a_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_the_logged_in_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def _login(client, email, password):
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
