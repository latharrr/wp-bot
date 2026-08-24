"""Ported from the reference repo: best-effort SMTP alert when the WhatsApp session logs out.
Never raises on missing/incomplete SMTP config -- logs a warning and skips silently instead,
matching the reference repo's documented behavior."""
import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_logout_alert(phone_number: str | None, status_code: int | None) -> None:
    settings = get_settings()
    recipients = settings.alert_recipient_list

    if not (settings.smtp_host and settings.smtp_username and settings.smtp_password and recipients):
        logger.warning("SMTP not fully configured; skipping logout alert email")
        return

    subject = "wp-bot: WhatsApp session logged out"
    body = (
        f"The WhatsApp bridge session was logged out.\n\n"
        f"Phone number: {phone_number or 'unknown'}\n"
        f"Status code: {status_code}\n\n"
        f"Re-pair the session from the dashboard to resume live ingestion."
    )
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email or settings.smtp_username
    message["To"] = ", ".join(recipients)

    try:
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
        with server:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(message["From"], recipients, message.as_string())
    except Exception:
        logger.exception("Failed to send logout alert email")
