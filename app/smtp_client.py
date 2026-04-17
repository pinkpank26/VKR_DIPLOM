import ssl
import smtplib
from email.message import EmailMessage
from email.header import Header
from email.utils import formataddr
from .config import settings


def send_email(to_email: str, subject: str, body: str) -> tuple[bool, str | None, str | None]:
    msg = EmailMessage()

    msg["From"] = formataddr(
        (str(Header(settings.SMTP_FROM_NAME, "utf-8")), settings.SMTP_FROM_EMAIL)
    )
    msg["To"] = to_email
    msg["Subject"] = str(Header(subject, "utf-8"))
    msg.set_content(body, charset="utf-8")

    context = ssl.create_default_context()

    try:
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

        return True, None, None

    except smtplib.SMTPResponseException as e:
        smtp_reply = e.smtp_error.decode("utf-8", errors="ignore") if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        return False, str(e.smtp_code), smtp_reply
    except Exception as e:
        return False, None, str(e)