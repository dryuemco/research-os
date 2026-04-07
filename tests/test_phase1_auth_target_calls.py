from sqlalchemy import text


def _login(client, username: str, password: str) -> str:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_success(client):
    response = client.post(
        "/auth/login",
        json={"username": "admin1", "password": "dev-admin1-placeholder-change-me"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "admin1"
    assert body["token_type"] == "bearer"


def test_login_failure(client):
    response = client.post(
        "/auth/login",
        json={"username": "admin1", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_seeded_admin_users_exist(client, db_session):
    rows = db_session.execute(
        text("SELECT username, role FROM users WHERE username IN ('admin1', 'admin2')")
    ).fetchall()
    usernames = {row[0] for row in rows}
    assert usernames == {"admin1", "admin2"}


def test_admin_access_allowed_and_unauthorized_denied(client):
    without_auth = client.get(
        "/target-calls",
        headers={"X-Internal-Api-Key": "invalid", "X-User-Id": "nobody"},
    )
    assert without_auth.status_code == 401

    token = _login(client, "admin1", "dev-admin1-placeholder-change-me")
    with_auth = client.get("/target-calls", headers={"Authorization": f"Bearer {token}"})
    assert with_auth.status_code == 200


def test_create_list_update_target_call(client):
    token = _login(client, "admin1", "dev-admin1-placeholder-change-me")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/target-calls",
        headers=headers,
        json={
            "title": "Cluster 1 Health AI",
            "programme": "horizon",
            "call_url": "https://example.org/calls/1",
            "summary": "Manual target for partner scouting",
            "status": "draft",
        },
    )
    assert created.status_code == 200
    target_call_id = created.json()["id"]

    listed = client.get("/target-calls", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == target_call_id for item in listed.json())

    updated = client.patch(
        f"/target-calls/{target_call_id}",
        headers=headers,
        json={"status": "active", "summary": "Refined manually"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "active"


def test_target_call_validation_failures(client):
    token = _login(client, "admin1", "dev-admin1-placeholder-change-me")
    headers = {"Authorization": f"Bearer {token}"}

    missing_title = client.post(
        "/target-calls",
        headers=headers,
        json={"programme": "horizon", "call_url": "https://example.org/x"},
    )
    assert missing_title.status_code == 422

    missing_source = client.post(
        "/target-calls",
        headers=headers,
        json={"title": "x", "programme": "horizon"},
    )
    assert missing_source.status_code == 422
