import smtplib


def test_send_returns_false_when_smtp_not_configured(client):
    # conftest đã set SMTP_USER="" -> không cấu hình.
    from app.shared import mailer

    assert mailer.send_account_email("a@b.com", "Tên", "pw123") is False


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
