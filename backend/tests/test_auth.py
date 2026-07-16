def test_register_success(client):
    response = client.post(
        "/register",
        json={"username": "alice", "email": "alice@example.com", "password": "supersecret1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_duplicate_email_rejected(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "supersecret1"}
    first = client.post("/register", json=payload)
    assert first.status_code == 201

    second = client.post(
        "/register",
        json={"username": "someoneelse", "email": "bob@example.com", "password": "anotherpass1"},
    )
    assert second.status_code == 409


def test_register_duplicate_username_rejected(client):
    client.post(
        "/register",
        json={"username": "carol", "email": "carol@example.com", "password": "supersecret1"},
    )
    response = client.post(
        "/register",
        json={"username": "carol", "email": "different@example.com", "password": "supersecret1"},
    )
    assert response.status_code == 409


def test_login_success(client):
    client.post(
        "/register",
        json={"username": "dave", "email": "dave@example.com", "password": "correcthorse1"},
    )
    response = client.post("/login", json={"email": "dave@example.com", "password": "correcthorse1"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_login_wrong_password_rejected(client):
    client.post(
        "/register",
        json={"username": "erin", "email": "erin@example.com", "password": "correcthorse1"},
    )
    response = client.post("/login", json={"email": "erin@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_nonexistent_user_rejected(client):
    response = client.post("/login", json={"email": "nobody@example.com", "password": "whatever1"})
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/me")
    assert response.status_code in (401, 403)  # 403 if no Authorization header is sent at all


def test_me_returns_current_user_with_valid_token(client):
    client.post(
        "/register",
        json={"username": "frank", "email": "frank@example.com", "password": "correcthorse1"},
    )
    login_response = client.post("/login", json={"email": "frank@example.com", "password": "correcthorse1"})
    token = login_response.json()["access_token"]

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "frank"


def test_me_rejects_garbage_token(client):
    response = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
