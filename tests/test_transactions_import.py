def _upload(client, headers, csv_text):
    return client.post(
        "/transactions/import",
        headers=headers,
        files={"file": ("transactions.csv", csv_text.encode("utf-8"), "text/csv")},
    )


def test_import_valid_rows(client, auth_headers, categories):
    csv_text = (
        "date,description,category,amount\n"
        "2026-01-01,Paycheck,Salary,2000.00\n"
        "2026-01-02,Groceries,Food,-45.50\n"
    )
    response = _upload(client, auth_headers, csv_text)
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 2
    assert body["imported_count"] == 2
    assert body["failed_count"] == 0
    assert [r["status"] for r in body["results"]] == ["imported", "imported"]

    transactions = client.get("/transactions/", headers=auth_headers).json()
    assert len(transactions) == 2


def test_import_reports_per_row_errors_without_failing_whole_file(client, auth_headers, categories):
    csv_text = (
        "date,description,category,amount\n"
        "2026-01-01,Good row,Food,-10.00\n"
        "2026-01-02,Unknown category,Nonexistent,-10.00\n"
        "2026-01-03,Wrong sign,Food,10.00\n"
        "not-a-date,Bad date column,Food,-10.00\n"
        "2026-01-05,Bad amount,Food,not-a-number\n"
    )
    response = _upload(client, auth_headers, csv_text)
    body = response.json()

    assert body["total_rows"] == 5
    assert body["imported_count"] == 1  # only the first row is valid
    assert body["failed_count"] == 4

    by_row = {r["row_number"]: r for r in body["results"]}
    assert by_row[2]["status"] == "imported"  # header is row 1, first data row is row 2
    assert "Unknown category" in by_row[3]["error"]
    assert "negative" in by_row[4]["error"]
    assert "Invalid date" in by_row[5]["error"]
    assert "Invalid amount" in by_row[6]["error"]


def test_import_requires_csv_file_extension(client, auth_headers):
    response = client.post(
        "/transactions/import",
        headers=auth_headers,
        files={"file": ("transactions.txt", b"date,description,category,amount\n", "text/plain")},
    )
    assert response.status_code == 400


def test_import_rejects_missing_columns(client, auth_headers):
    response = _upload(client, auth_headers, "date,amount\n2026-01-01,10.00\n")
    assert response.status_code == 400
    assert "missing required column" in response.json()["detail"]


def test_import_skips_blank_trailing_rows(client, auth_headers, categories):
    csv_text = "date,description,category,amount\n2026-01-01,Groceries,Food,-10.00\n\n\n"
    response = _upload(client, auth_headers, csv_text)
    body = response.json()
    assert body["total_rows"] == 1
    assert body["imported_count"] == 1


def test_import_only_matches_the_uploading_users_own_categories(client, auth_headers, categories):
    client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    other_headers = {
        "Authorization": "Bearer "
        + client.post(
            "/auth/login", json={"email": "other@example.com", "password": "password123"}
        ).json()["access_token"]
    }

    response = _upload(client, other_headers, "date,description,category,amount\n2026-01-01,x,Food,-10.00\n")
    body = response.json()
    # "other" has their own auto-seeded "Food" category, so this succeeds
    # against *their* category, never touching the first user's data.
    assert body["imported_count"] == 1
    assert client.get("/transactions/", headers=auth_headers).json() == []
