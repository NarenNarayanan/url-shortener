CHROME_WINDOWS_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)
SAFARI_IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
)


def _register_and_login(client, username, email):
    client.post("/register", json={"username": username, "email": email, "password": "supersecret1"})
    login = client.post("/login", json={"email": email, "password": "supersecret1"})
    return login.json()["access_token"]


def test_analytics_requires_authentication(client):
    response = client.get("/urls/whatever/analytics")
    assert response.status_code in (401, 403)


def test_analytics_for_unowned_or_missing_code_returns_404(client):
    token = _register_and_login(client, "analyticsuser", "analyticsuser@example.com")
    response = client.get("/urls/doesnotexist/analytics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_analytics_records_browser_os_device_breakdown(client):
    token = _register_and_login(client, "uaowner", "uaowner@example.com")
    created = client.post(
        "/urls",
        json={"original_url": "https://example.com/analytics-target"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    short_code = created["short_code"]

    client.get(f"/{short_code}", headers={"User-Agent": CHROME_WINDOWS_UA}, follow_redirects=False)
    client.get(f"/{short_code}", headers={"User-Agent": CHROME_WINDOWS_UA}, follow_redirects=False)
    client.get(f"/{short_code}", headers={"User-Agent": SAFARI_IPHONE_UA}, follow_redirects=False)

    response = client.get(f"/urls/{short_code}/analytics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()

    assert body["short_code"] == short_code
    assert body["total_clicks"] == 3

    browsers = {item["label"]: item["count"] for item in body["by_browser"]}
    assert browsers.get("Chrome") == 2
    assert browsers.get("Mobile Safari") == 1

    device_types = {item["label"]: item["count"] for item in body["by_device_type"]}
    assert device_types.get("desktop") == 2
    assert device_types.get("mobile") == 1

    oses = {item["label"] for item in body["by_os"]}
    assert "Windows" in oses
    assert "iOS" in oses


def test_analytics_clicks_over_time_has_entries_after_a_click(client):
    token = _register_and_login(client, "timeowner", "timeowner@example.com")
    created = client.post(
        "/urls",
        json={"original_url": "https://example.com/time-series"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    short_code = created["short_code"]

    client.get(f"/{short_code}", follow_redirects=False)

    response = client.get(
        f"/urls/{short_code}/analytics?days=7&group_by=day",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()
    assert body["group_by"] == "day"
    assert len(body["clicks_over_time"]) == 1
    assert body["clicks_over_time"][0]["count"] == 1


def test_analytics_group_by_week_accepted(client):
    token = _register_and_login(client, "weekowner", "weekowner@example.com")
    created = client.post(
        "/urls",
        json={"original_url": "https://example.com/weekly"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    short_code = created["short_code"]

    client.get(f"/{short_code}", follow_redirects=False)

    response = client.get(
        f"/urls/{short_code}/analytics?group_by=week",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["group_by"] == "week"
