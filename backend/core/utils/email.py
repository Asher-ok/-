import smtplib
import socket
import ipaddress
import imaplib
import time
from email import policy
from email.utils import formatdate, make_msgid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Iterable, Optional

from core.config import settings


def _try_append_to_sent(msg: MIMEMultipart) -> None:
    if not getattr(settings, "smtp_save_to_sent", False):
        return

    from_email = settings.smtp_from_email or settings.smtp_user
    if not from_email or not settings.smtp_user or not settings.smtp_password:
        return

    domain = ""
    if "@" in settings.smtp_user:
        domain = settings.smtp_user.split("@", 1)[1].strip()

    host_candidates: list[str] = []
    if getattr(settings, "imap_host", None):
        host_candidates.append(settings.imap_host)  # type: ignore[arg-type]
    if domain:
        host_candidates.append(f"imap.{domain}")
        host_candidates.append(f"mail.{domain}")

    timeout = 12
    folders: list[str] = []
    if getattr(settings, "imap_sent_folder", None):
        folders.append(settings.imap_sent_folder)  # type: ignore[arg-type]
    folders.extend(["已发送邮件", "已发送", "Sent", "Sent Items", "Sent Messages", "INBOX.Sent"])

    msg_bytes = msg.as_bytes(policy=policy.SMTP)
    internal_date = imaplib.Time2Internaldate(time.time())

    for host in [h for h in host_candidates if h]:
        imap = None
        try:
            try:
                if getattr(settings, "imap_use_ssl", True):
                    imap = imaplib.IMAP4_SSL(host, getattr(settings, "imap_port", 993), timeout=timeout)
                else:
                    imap = imaplib.IMAP4(host, getattr(settings, "imap_port", 143), timeout=timeout)
            except TypeError:
                if getattr(settings, "imap_use_ssl", True):
                    imap = imaplib.IMAP4_SSL(host, getattr(settings, "imap_port", 993))
                else:
                    imap = imaplib.IMAP4(host, getattr(settings, "imap_port", 143))

            imap.login(settings.smtp_user, settings.smtp_password)
            for folder in folders:
                try:
                    typ, _ = imap.append(folder, "\\Seen", internal_date, msg_bytes)
                    if typ == "OK":
                        return
                except Exception:
                    continue
        except Exception:
            continue
        finally:
            if imap is not None:
                try:
                    imap.logout()
                except Exception:
                    pass


def send_contact_email(
    subject: str,
    html_body: str,
    to_emails: Iterable[str],
    plain_body: Optional[str] = None,
    from_email: Optional[str] = None,
) -> None:
    """
    通过 SMTP 发送官网表单邮件。
    - 端口 465 使用 SSL
    - 其他端口使用 STARTTLS
    """
    if not settings.smtp_host:
        raise ValueError("SMTP host 未配置")
    if not settings.smtp_user or not settings.smtp_password:
        raise ValueError("SMTP 凭据未配置")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = (from_email or "").strip() or settings.smtp_from_email or settings.smtp_user
    msg["To"] = ", ".join(to_emails)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()

    if plain_body:
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    timeout = 12
    host_candidates = [settings.smtp_host]
    is_ip = False
    try:
        ipaddress.ip_address(settings.smtp_host)
        is_ip = True
    except ValueError:
        is_ip = False

    if not is_ip:
        if settings.smtp_host.startswith("smtp."):
            host_candidates.append(settings.smtp_host.replace("smtp.", "mail.", 1))
        elif not settings.smtp_host.startswith("mail."):
            host_candidates.append(f"smtp.{settings.smtp_host}")

    attempts: list[tuple[str, int]] = []
    for host in host_candidates:
        attempts.append((host, settings.smtp_port))
        if settings.smtp_port != 465:
            attempts.append((host, 465))
        if settings.smtp_port != 25:
            attempts.append((host, 25))

    errors: list[str] = []
    for host, port in attempts:
        try:
            if port == 465:
                with smtplib.SMTP_SSL(host, port, timeout=timeout) as server:
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.sendmail(msg["From"], list(to_emails), msg.as_string())
                try:
                    _try_append_to_sent(msg)
                except Exception:
                    pass
            else:
                with smtplib.SMTP(host, port, timeout=timeout) as server:
                    server.ehlo()
                    if server.has_extn("starttls"):
                        server.starttls()
                        server.ehlo()

                    login_exc: Exception | None = None
                    try:
                        server.login(settings.smtp_user, settings.smtp_password)
                    except (smtplib.SMTPNotSupportedError, smtplib.SMTPAuthenticationError) as exc:
                        login_exc = exc

                    if login_exc and port != 25:
                        raise login_exc

                    server.sendmail(msg["From"], list(to_emails), msg.as_string())
                try:
                    _try_append_to_sent(msg)
                except Exception:
                    pass
            return
        except (ConnectionRefusedError, socket.timeout, socket.gaierror, OSError, smtplib.SMTPException) as exc:
            errors.append(f"{host}:{port} -> {exc}")

    raise ValueError("SMTP发送失败: " + " | ".join(errors))
