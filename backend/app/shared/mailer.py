"""Gửi email qua Gmail SMTP (App Password).

Dùng cho FR: Admin tạo tài khoản -> gửi thông tin đăng nhập cho người dùng.
KHÔNG log mật khẩu (CLAUDE.md quy tắc 8).
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_account_email(to: str, full_name: str, password: str) -> bool:
    """Gửi email + mật khẩu tạm cho tài khoản mới. True nếu gửi thành công.

    SMTP chưa cấu hình -> False ngay; caller sẽ trả temp_password cho Admin
    để gửi tay (không chặn luồng tạo tài khoản khi demo).
    """
    if not settings.smtp_user or not settings.smtp_password:
        return False

    body = (
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
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "🎉 Tài khoản của bạn đã được duyệt — Maple"
    msg["From"] = settings.mail_from or settings.smtp_user
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True
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
