"""Gửi email thông báo duyệt tài khoản.

Hai đường gửi, chọn theo cấu hình:
- BREVO_API_KEY có giá trị -> Brevo API qua HTTPS (bắt buộc trên Render free
  vì host này chặn kết nối SMTP ra ngoài: OSError 101 Network is unreachable).
- Ngược lại nếu có SMTP_USER/SMTP_PASSWORD -> Gmail SMTP (chạy local).

KHÔNG log mật khẩu (CLAUDE.md quy tắc 8).
"""
import json
import logging
import smtplib
import urllib.request
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)

_SUBJECT = "🎉 Tài khoản của bạn đã được duyệt — Maple"
_ADMIN_SUBJECT = "🔔 Yêu cầu tài khoản mới — Maple"


def _build_body(to: str, full_name: str, password: str) -> str:
    return (
        f"Xin chào {full_name},\n\n"
        "Chúc mừng! Tài khoản của bạn đã được Quản trị viên DUYỆT THÀNH CÔNG "
        "trên hệ thống Maple 🍁.\n\n"
        "Thông tin đăng nhập của bạn:\n"
        f"  • Email:    {to}\n"
        f"  • Mật khẩu: {password}\n\n"
        f"Đăng nhập tại: {settings.app_login_url}\n"
        'Bạn cũng có thể bấm "Đăng nhập bằng Google" với chính email này — '
        "không cần nhớ mật khẩu.\n\n"
        "Mẹo: sau khi đăng nhập, bạn có thể vào ngay mục Chat để hỏi đáp "
        "dựa trên tài liệu môn học.\n\n"
        "-- Maple 🍁 — Trợ lý học tập AI"
    )


def _send_via_brevo(to: str, body: str, subject: str = _SUBJECT) -> bool:
    payload = {
        "sender": {
            "name": "Maple",
            "email": settings.mail_from or settings.smtp_user,
        },
        "to": [{"email": to}],
        "subject": subject,
        "textContent": body,
    }
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": settings.brevo_api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return 200 <= res.status < 300


def _send_via_smtp(to: str, body: str, subject: str = _SUBJECT) -> bool:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.mail_from or settings.smtp_user
    msg["To"] = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    return True


def _send(to: str, body: str, subject: str) -> bool:
    """Chọn đường gửi (Brevo ưu tiên, fallback SMTP). False nếu chưa cấu hình."""
    if settings.brevo_api_key:
        return _send_via_brevo(to, body, subject)
    if settings.smtp_user and settings.smtp_password:
        return _send_via_smtp(to, body, subject)
    return False


def send_account_email(to: str, full_name: str, password: str) -> bool:
    """Gửi email duyệt thành công kèm mật khẩu tạm. True nếu gửi được.

    Chưa cấu hình Brevo lẫn SMTP -> False ngay; caller trả temp_password
    cho Admin gửi tay (không chặn luồng tạo tài khoản).
    """
    body = _build_body(to, full_name, password)
    try:
        return _send(to, body, _SUBJECT)
    except Exception as e:
        # Ghi loại lỗi + thông điệp để chẩn đoán (auth sai / cổng bị chặn /
        # timeout...). KHÔNG log mật khẩu.
        logger.warning(
            "Gửi email cấp tài khoản tới %s thất bại: %s: %s",
            to,
            type(e).__name__,
            e,
        )
        return False


def send_admin_new_request_email(
    requester_name: str, requester_email: str, requested_role: str, message: str
) -> bool:
    """Báo cho Admin (settings.admin_email) biết có yêu cầu tài khoản mới.

    Best-effort: trả False nếu chưa cấu hình mail hoặc chưa đặt ADMIN_EMAIL;
    caller KHÔNG chặn luồng lưu yêu cầu khi gửi thất bại.
    """
    admin_to = settings.admin_email
    if not admin_to:
        return False
    body = (
        "Có một yêu cầu cấp tài khoản mới trên hệ thống Maple 🍁.\n\n"
        f"  • Họ tên:  {requester_name}\n"
        f"  • Email:   {requester_email}\n"
        f"  • Vai trò: {requested_role}\n"
        f"  • Lời nhắn: {message or '(không có)'}\n\n"
        "Vào trang Quản lý người dùng → tab 'Yêu cầu chờ duyệt' để Duyệt "
        "hoặc Từ chối:\n"
        f"  {settings.app_login_url}\n\n"
        "-- Maple 🍁 — Trợ lý học tập AI"
    )
    try:
        return _send(admin_to, body, _ADMIN_SUBJECT)
    except Exception as e:
        logger.warning(
            "Gửi email báo yêu cầu tài khoản tới admin thất bại: %s: %s",
            type(e).__name__,
            e,
        )
        return False
