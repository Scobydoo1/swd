def test_public_register_removed(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "any@x.com", "password": "pw", "full_name": "Any"},
    )
    assert res.status_code in (404, 405)


def _patch_google_verify(monkeypatch, email: str, verified: bool = True):
    """Mock google-auth verify: trả payload với email cho trước."""
    from app.modules.auth import service as auth_service

    monkeypatch.setattr(
        auth_service.google_id_token,
        "verify_oauth2_token",
        lambda token, request, audience: {
            "email": email,
            "email_verified": verified,
        },
    )


def _enable_google(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "google_oauth_client_id", "test-client-id")


def test_google_login_not_configured_returns_503(client):
    res = client.post("/api/auth/google", json={"id_token": "any"})
    assert res.status_code == 503


def test_google_login_unknown_email_403(client, monkeypatch):
    _enable_google(monkeypatch)
    _patch_google_verify(monkeypatch, "stranger@gmail.com")
    res = client.post("/api/auth/google", json={"id_token": "fake"})
    assert res.status_code == 403


def test_google_login_known_email_returns_jwt(client, monkeypatch, admin_headers):
    # admin_headers fixture đảm bảo admin@maple-tests.com tồn tại trong DB.
    _enable_google(monkeypatch)
    _patch_google_verify(monkeypatch, "admin@maple-tests.com")
    res = client.post("/api/auth/google", json={"id_token": "fake"})
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"]
    assert data["user"]["email"] == "admin@maple-tests.com"


def test_google_login_unverified_email_401(client, monkeypatch, admin_headers):
    # Email Google chưa xác minh -> từ chối kể cả khi tài khoản tồn tại.
    _enable_google(monkeypatch)
    _patch_google_verify(monkeypatch, "admin@maple-tests.com", verified=False)
    res = client.post("/api/auth/google", json={"id_token": "fake"})
    assert res.status_code == 401


def test_google_login_invalid_token_401(client, monkeypatch):
    from app.modules.auth import service as auth_service

    _enable_google(monkeypatch)

    def raise_invalid(token, request, audience):
        raise ValueError("invalid token")

    monkeypatch.setattr(
        auth_service.google_id_token, "verify_oauth2_token", raise_invalid
    )
    res = client.post("/api/auth/google", json={"id_token": "bad"})
    assert res.status_code == 401
