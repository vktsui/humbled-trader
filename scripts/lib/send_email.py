#!/usr/bin/env python3
"""
Shared email sender for Humbled Trader scanners.

Sends via SMTP using credentials from environment / .env. Defaults to Gmail.
Usable as a module (send_email) or CLI:

    echo "body" | python3 scripts/lib/send_email.py "Subject line"

Required env (set in .env):
    EMAIL_TO        recipient (default vktsui@gmail.com)
    EMAIL_FROM      sender address (default = SMTP_USER)
    SMTP_HOST       default smtp.gmail.com
    SMTP_PORT       default 587 (STARTTLS)
    SMTP_USER       SMTP login (your Gmail address)
    SMTP_PASS       Gmail App Password (not your normal password)
"""

from __future__ import annotations

import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

DEFAULT_TO = "vktsui@gmail.com"


def load_env() -> None:
    # .env lives at project root (two levels up from scripts/lib/)
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def send_email(subject: str, body: str) -> bool:
    load_env()

    to_addr = os.environ.get("EMAIL_TO", DEFAULT_TO)
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("EMAIL_FROM", smtp_user or to_addr)
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))

    if not smtp_user or not smtp_pass:
        print(
            "Email skipped: set SMTP_USER and SMTP_PASS (Gmail App Password) in .env",
            file=sys.stderr,
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as s:
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls(context=context)
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        print(f"Email sent to {to_addr}")
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"Email send failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    subject = sys.argv[1] if len(sys.argv) > 1 else "Humbled Trader Alert"
    body = sys.stdin.read()
    return 0 if send_email(subject, body) else 1


if __name__ == "__main__":
    sys.exit(main())
