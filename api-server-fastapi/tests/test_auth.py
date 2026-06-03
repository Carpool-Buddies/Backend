from tests.conftest import make_user, auth_cookies


def test_me_requires_auth(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_with_valid_cookie(client, session):
    user = make_user(session)
    res = client.get("/api/v1/auth/me", cookies=auth_cookies(user))
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "student@post.bgu.ac.il"
    assert body["org"] == "BGU"
    assert body["org_name_he"]  # resolved Hebrew name present


def test_me_with_bad_token(client):
    res = client.get("/api/v1/auth/me", cookies={"access_token": "garbage"})
    assert res.status_code == 401


def test_onboarding_updates_user(client, session):
    user = make_user(session, full_name="Old Name", onboarded=False)
    res = client.post(
        "/api/v1/auth/onboarding",
        json={"full_name": "New Name", "org": "TAU"},
        cookies=auth_cookies(user),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["full_name"] == "New Name"
    assert body["org"] == "TAU"
    assert body["onboarded"] is True


def test_logout_clears_cookies(client, session):
    user = make_user(session)
    res = client.post("/api/v1/auth/logout", cookies=auth_cookies(user))
    assert res.status_code == 200


def test_oauth_login_redirects(client):
    res = client.get("/api/v1/auth/google/login", follow_redirects=False)
    assert res.status_code in (302, 307)
    assert "accounts.google.com" in res.headers["location"]


def test_unknown_provider_404(client):
    res = client.get("/api/v1/auth/twitter/login", follow_redirects=False)
    assert res.status_code == 404
