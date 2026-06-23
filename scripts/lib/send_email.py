#!/usr/bin/env python3
"""
Shared email sender for Humbled Trader scanners.

Backend is auto-selected from whichever credentials are present in .env:
  1. RESEND_API_KEY    -> Resend HTTP API   (recommended, no SMTP password)
  2. SENDGRID_API_KEY  -> SendGrid HTTP API
  3. SMTP_USER + SMTP_PASS -> SMTP (e.g. Gmail App Password)

Usable as a module (send_email) or CLI:
    echo "body" | python3 scripts/lib/send_email.py "Subject line"

Common env (set in .env):
    EMAIL_TO     recipient (default vktsui@gmail.com)
    EMAIL_FROM   sender address (provider-dependent, see .env.example)
"""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import sys
import urllib.error
import urllib.request
from email.message import EmailMessage
from pathlib import Path

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

DEFAULT_TO = "vktsui@gmail.com"


def load_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def _post_json(url: str, headers: dict, payload: dict) -> tuple[int, str]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20, context=_SSL_CTX) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def _send_resend(subject: str, body: str, to_addr: str) -> bool:
    api_key = os.environ["RESEND_API_KEY"]
    # Free tier with no verified domain can send from onboarding@resend.dev
    from_addr = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")
    status, resp = _post_json(
        "https://api.resend.com/emails",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {"from": from_addr, "to": [to_addr], "subject": subject, "text": body},
    )
    if 200 <= status < 300:
        print(f"Email sent to {to_addr} via Resend")
        return True
    print(f"Resend failed (HTTP {status}): {resp}", file=sys.stderr)
    return False


def _send_sendgrid(subject: str, body: str, to_addr: str) -> bool:
    api_key = os.environ["SENDGRID_API_KEY"]
    from_addr = os.environ.get("EMAIL_FROM", to_addr)
    status, resp = _post_json(
        "https://api.sendgrid.com/v3/mail/send",
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {
            "personalizations": [{"to": [{"email": to_addr}]}],
            "from": {"email": from_addr},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        },
    )
    if 200 <= status < 300:
        print(f"Email sent to {to_addr} via SendGrid")
        return True
    print(f"SendGrid failed (HTTP {status}): {resp}", file=sys.stderr)
    return False


def _send_smtp(subject: str, body: str, to_addr: str) -> bool:
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    from_addr = os.environ.get("EMAIL_FROM", smtp_user)
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=_SSL_CTX, timeout=20) as s:
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls(context=_SSL_CTX)
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        print(f"Email sent to {to_addr} via SMTP")
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"SMTP failed: {e}", file=sys.stderr)
        return False


def send_email(subject: str, body: str) -> bool:
    load_env()
    to_addr = os.environ.get("EMAIL_TO", DEFAULT_TO)

    if os.environ.get("RESEND_API_KEY"):
        return _send_resend(subject, body, to_addr)
    if os.environ.get("SENDGRID_API_KEY"):
        return _send_sendgrid(subject, body, to_addr)
    if os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS"):
        return _send_smtp(subject, body, to_addr)

    print(
        "Email skipped: set RESEND_API_KEY (recommended), SENDGRID_API_KEY, "
        "or SMTP_USER+SMTP_PASS in .env",
        file=sys.stderr,
    )
    return False


def main() -> int:
    subject = sys.argv[1] if len(sys.argv) > 1 else "Humbled Trader Alert"
    body = sys.stdin.read()
    return 0 if send_email(subject, body) else 1


if __name__ == "__main__":
    sys.exit(main())
