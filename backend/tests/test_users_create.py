def test_admin_creates_user_smtp_off_returns_temp_password(client, admin_headers):
    res = client.post(
        "/api/users",
        json={"email": "newsv@uni.edu", "full_name": "Sinh Viên Mới", "role": "USER"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == "newsv@uni.edu"
    assert data["user"]["role"] == "USER"
    assert data["email_sent"] is False
    # SMTP tắt -> trả mật khẩu tạm để Admin gửi tay.
    assert isinstance(data["temp_password"], str) and len(data["temp_password"]) >= 8


def test_created_user_can_login_with_temp_password(client, admin_headers):
    res = client.post(
        "/api/users",
        json={
            "email": "newgv@uni.edu",
            "full_name": "Giảng Viên Mới",
            "role": "LECTURER",
        },
        headers=admin_headers,
    )
    password = res.json()["temp_password"]
    login = client.post(
        "/api/auth/login",
        data={"username": "newgv@uni.edu", "password": password},
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "LECTURER"


def test_email_sent_hides_temp_password(client, admin_headers, monkeypatch):
    from app.shared import mailer

    monkeypatch.setattr(mailer, "send_account_email", lambda *a, **kw: True)
    res = client.post(
        "/api/users",
        json={"email": "mailok@uni.edu", "full_name": "Mail OK", "role": "USER"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    assert res.json()["email_sent"] is True
    assert res.json()["temp_password"] is None


def test_duplicate_email_400(client, admin_headers):
    payload = {"email": "dup@uni.edu", "full_name": "Dup", "role": "USER"}
    assert (
        client.post("/api/users", json=payload, headers=admin_headers).status_code
        == 201
    )
    assert (
        client.post("/api/users", json=payload, headers=admin_headers).status_code
        == 400
    )


def test_non_admin_cannot_create(client, student_headers):
    res = client.post(
        "/api/users",
        json={"email": "x@uni.edu", "full_name": "X", "role": "USER"},
        headers=student_headers,
    )
    assert res.status_code == 403


def test_cannot_create_admin_role(client, admin_headers):
    res = client.post(
        "/api/users",
        json={"email": "evil@uni.edu", "full_name": "Evil", "role": "ADMIN"},
        headers=admin_headers,
    )
    assert res.status_code == 422
