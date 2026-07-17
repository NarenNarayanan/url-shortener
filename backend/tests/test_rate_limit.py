from app.rate_limit import limiter


def test_login_rate_limit_returns_429_after_threshold(client):
    # Every other test in the suite runs with the limiter disabled (see
    # conftest.py) — this is the one test that turns it on to prove the
    # limiting itself actually works, then turns it back off so it doesn't
    # affect any test that runs after it.
    limiter.enabled = True
    try:
        client.post(
            "/register",
            json={"username": "ratelimited", "email": "ratelimited@example.com", "password": "supersecret1"},
        )

        responses = [
            client.post("/login", json={"email": "ratelimited@example.com", "password": "wrongpassword"})
            for _ in range(6)
        ]

        assert [r.status_code for r in responses[:5]] == [401] * 5
        assert responses[5].status_code == 429
    finally:
        limiter.enabled = False


def test_create_url_rate_limit_is_keyed_per_user_not_ip(client):
    """
    Two different users hitting the same limiter from the same client (same
    IP, since TestClient has no real network) should each get their own
    20/minute quota — proving the key is the user id, not the IP. If this
    were still IP-keyed, user B would already be rate limited by user A's
    requests before making any of their own.
    """
    # Register/login happen with the limiter still disabled — login has its
    # own 5/minute IP limit, and that bucket may already be partly used up
    # by test_login_rate_limit_returns_429_after_threshold above (Redis
    # isn't flushed between individual tests, only once per session).
    token_a = _register_and_login(client, username="quota_a", email="quota_a@example.com")
    token_b = _register_and_login(client, username="quota_b", email="quota_b@example.com")

    limiter.enabled = True
    try:
        headers_a = {"Authorization": f"Bearer {token_a}"}
        for i in range(20):
            response = client.post(
                "/urls", json={"original_url": f"https://example.com/a{i}"}, headers=headers_a
            )
            assert response.status_code == 201
        assert client.post(
            "/urls", json={"original_url": "https://example.com/a-over"}, headers=headers_a
        ).status_code == 429

        headers_b = {"Authorization": f"Bearer {token_b}"}
        response = client.post("/urls", json={"original_url": "https://example.com/b0"}, headers=headers_b)
        assert response.status_code == 201, "user B should have their own quota, not share user A's"
    finally:
        limiter.enabled = False


def _register_and_login(client, username, email):
    client.post("/register", json={"username": username, "email": email, "password": "supersecret1"})
    return client.post("/login", json={"email": email, "password": "supersecret1"}).json()["access_token"]
