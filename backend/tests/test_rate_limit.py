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
