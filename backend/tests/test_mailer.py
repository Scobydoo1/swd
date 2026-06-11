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

    monkeypatch.setattr(settings, "smtp_user", "bot@gmail.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is True
    assert sent == {
        "host": "smtp.gmail.com",
        "login": "bot@gmail.com",
        "to": "sv@uni.edu",
    }


def test_send_returns_false_on_smtp_error(client, monkeypatch):
    from app.config import settings
    from app.shared import mailer

    def boom(*a, **kw):
        raise OSError("connection refused")

    monkeypatch.setattr(settings, "smtp_user", "bot@gmail.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(smtplib, "SMTP_SSL", boom)

    assert mailer.send_account_email("sv@uni.edu", "Sinh Viên", "pw123") is False
