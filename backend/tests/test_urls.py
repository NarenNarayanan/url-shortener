from app.models import URL


def _register_and_login(client, username="alice", email="alice@example.com"):
    client.post(
        "/register",
        json={"username": username, "email": email, "password": "supersecret1"},
    )
    login = client.post("/login", json={"email": email, "password": "supersecret1"})
    return login.json()["access_token"]


def test_create_url_requires_authentication(client):
    response = client.post("/urls", json={"original_url": "https://example.com"})
    assert response.status_code in (401, 403)


def test_create_url_success(client):
    token = _register_and_login(client)
    response = client.post(
        "/urls",
        json={"original_url": "https://example.com/some/path"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["short_code"]) == 7
    assert body["short_url"].endswith(body["short_code"])
    assert body["original_url"] == "https://example.com/some/path"
    assert body["click_count"] == 0
    assert body["is_expired"] is False


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/doesnotexist", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_follows_to_original_url_and_counts_click(client, db_session):
    token = _register_and_login(client)
    create_response = client.post(
        "/urls",
        json={"original_url": "https://example.com/target"},
        headers={"Authorization": f"Bearer {token}"},
    )
    short_code = create_response.json()["short_code"]

    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/target"

    db_session.expire_all()
    url = db_session.query(URL).filter(URL.short_code == short_code).one()
    assert url.click_count == 1
    assert url.last_clicked_at is not None


def test_redirect_expired_url_returns_410(client):
    token = _register_and_login(client)
    create_response = client.post(
        "/urls",
        json={
            "original_url": "https://example.com/expired",
            "expires_at": "2000-01-01T00:00:00Z",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    short_code = create_response.json()["short_code"]

    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 410
