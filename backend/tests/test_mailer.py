import json
import smtplib


def test_send_returns_false_when_nothing_configured(client):
    # conftest đã set SMTP_USER="" và BREVO_API_KEY="" -> không cấu hình gì.
    from app.shared import mailer

    assert mailer.send_account_email("a@b.com", "Tên", "pw123") is False


def test_send_success_via_brevo_api(client, monkeypatch):
    """Có BREVO_API_KEY -> gửi qua HTTPS API (Render free chặn cổng SMTP)."""
    import urllib.request

    from app.config import settings
    from app.shared import mailer

    captured = {}

    class FakeResponse:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["api_key"] = req.headers.get("Api-key")
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(settings, "brevo_api_key", "xkeysib-test")
    monkeypatch.setattr(settings, "mail_from", "bot@gmail.com")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is True
    assert captured["url"] == "https://api.brevo.com/v3/smtp/email"
    assert captured["api_key"] == "xkeysib-test"
    payload = captured["payload"]
    assert payload["sender"]["email"] == "bot@gmail.com"
    assert payload["to"] == [{"email": "sv@uni.edu"}]
    assert "duyệt" in payload["subject"].lower()
    assert "DUYỆT THÀNH CÔNG" in payload["textContent"]
    assert "pw123" in payload["textContent"]


def test_brevo_api_error_returns_false(client, monkeypatch):
    import urllib.request

    from app.config import settings
    from app.shared import mailer

    def boom(req, timeout=None):
        raise OSError("network down")

    monkeypatch.setattr(settings, "brevo_api_key", "xkeysib-test")
    monkeypatch.setattr(settings, "mail_from", "bot@gmail.com")
    monkeypatch.setattr(urllib.request, "urlopen", boom)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is False


def test_send_success_via_smtp(client, monkeypatch):
    from app.config import settings
    from app.shared import mailer

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            sent["host"] = host

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, user, password):
            sent["login"] = user

        def send_message(self, msg):
            sent["to"] = msg["To"]
            sent["subject"] = msg["Subject"]
            sent["body"] = msg.get_payload(decode=True).decode("utf-8")

    monkeypatch.setattr(settings, "smtp_user", "bot@gmail.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is True
    assert sent["host"] == "smtp.gmail.com"
    assert sent["login"] == "bot@gmail.com"
    assert sent["to"] == "sv@uni.edu"
    # Email phải là thông báo "duyệt thành công" kèm thông tin đăng nhập.
    assert "duyệt" in sent["subject"].lower()
    assert "DUYỆT THÀNH CÔNG" in sent["body"]
    assert "sv@uni.edu" in sent["body"]
    assert "pw123" in sent["body"]


def test_send_returns_false_on_smtp_error(client, monkeypatch):
    from app.config import settings
    from app.shared import mailer

    def boom(*a, **kw):
        raise OSError("connection refused")

    monkeypatch.setattr(settings, "smtp_user", "bot@gmail.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(smtplib, "SMTP_SSL", boom)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is False
