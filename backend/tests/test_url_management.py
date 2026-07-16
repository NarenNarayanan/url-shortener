from app.cache import redis_client


def _register_and_login(client, username, email):
    client.post("/register", json={"username": username, "email": email, "password": "supersecret1"})
    login = client.post("/login", json={"email": email, "password": "supersecret1"})
    return login.json()["access_token"]


def _create_url(client, token, original_url, **extra):
    return client.post(
        "/urls",
        json={"original_url": original_url, **extra},
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def test_list_urls_requires_authentication(client):
    response = client.get("/urls")
    assert response.status_code in (401, 403)


def test_list_urls_only_returns_current_users_urls(client):
    token_a = _register_and_login(client, "usera", "usera@example.com")
    token_b = _register_and_login(client, "userb", "userb@example.com")
    _create_url(client, token_a, "https://example.com/a")
    _create_url(client, token_b, "https://example.com/b")

    response = client.get("/urls", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["original_url"] == "https://example.com/a"


def test_list_urls_pagination(client):
    token = _register_and_login(client, "paginator", "paginator@example.com")
    for i in range(3):
        _create_url(client, token, f"https://example.com/page{i}")

    page1 = client.get("/urls?page=1&page_size=2", headers={"Authorization": f"Bearer {token}"}).json()
    assert page1["total"] == 3
    assert len(page1["items"]) == 2

    page2 = client.get("/urls?page=2&page_size=2", headers={"Authorization": f"Bearer {token}"}).json()
    assert len(page2["items"]) == 1


def test_list_urls_search_matches_original_url(client):
    token = _register_and_login(client, "searcher", "searcher@example.com")
    _create_url(client, token, "https://example.com/findme")
    _create_url(client, token, "https://example.com/other")

    response = client.get("/urls?search=findme", headers={"Authorization": f"Bearer {token}"})
    body = response.json()
    assert body["total"] == 1
    assert "findme" in body["items"][0]["original_url"]


def test_update_url_changes_original_url_and_invalidates_cache(client, db_session):
    token = _register_and_login(client, "editor", "editor@example.com")
    created = _create_url(client, token, "https://example.com/old")
    short_code = created["short_code"]

    # populate the cache
    client.get(f"/{short_code}", follow_redirects=False)
    assert redis_client.get(f"url:short_code:{short_code}") is not None

    response = client.patch(
        f"/urls/{short_code}",
        json={"original_url": "https://example.com/new"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["original_url"] == "https://example.com/new"
    assert redis_client.get(f"url:short_code:{short_code}") is None

    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.headers["location"] == "https://example.com/new"


def test_update_url_partial_update_does_not_clear_expires_at(client):
    token = _register_and_login(client, "partial", "partial@example.com")
    created = _create_url(client, token, "https://example.com/keep-expiry", expires_at="2030-01-01T00:00:00Z")
    short_code = created["short_code"]

    response = client.patch(
        f"/urls/{short_code}",
        json={"original_url": "https://example.com/keep-expiry-2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["expires_at"] is not None


def test_update_url_can_explicitly_clear_expires_at(client):
    token = _register_and_login(client, "clearer", "clearer@example.com")
    created = _create_url(client, token, "https://example.com/clear-expiry", expires_at="2030-01-01T00:00:00Z")
    short_code = created["short_code"]

    response = client.patch(
        f"/urls/{short_code}",
        json={"expires_at": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["expires_at"] is None


def test_update_url_other_users_link_returns_404(client):
    token_a = _register_and_login(client, "ownera", "ownera@example.com")
    token_b = _register_and_login(client, "ownerb", "ownerb@example.com")
    created = _create_url(client, token_a, "https://example.com/mine")

    response = client.patch(
        f"/urls/{created['short_code']}",
        json={"original_url": "https://example.com/hijacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


def test_delete_url_removes_it_and_invalidates_cache(client, db_session):
    token = _register_and_login(client, "deleter", "deleter@example.com")
    created = _create_url(client, token, "https://example.com/todelete")
    short_code = created["short_code"]

    client.get(f"/{short_code}", follow_redirects=False)
    assert redis_client.get(f"url:short_code:{short_code}") is not None

    response = client.delete(f"/urls/{short_code}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    assert redis_client.get(f"url:short_code:{short_code}") is None

    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 404


def test_delete_other_users_link_returns_404(client):
    token_a = _register_and_login(client, "victim", "victim@example.com")
    token_b = _register_and_login(client, "attacker", "attacker@example.com")
    created = _create_url(client, token_a, "https://example.com/protected")

    response = client.delete(f"/urls/{created['short_code']}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 404
