# Step 11 — Email alerts

Both scanners email results to **vktsui@gmail.com** after saving their JSON.

## Setup (Gmail)

1. Enable 2-Step Verification on your Google account.
2. Create an **App Password**: https://myaccount.google.com/apppasswords
3. Copy `.env.example` → `.env` and set:
   - `EMAIL_TO` (default `vktsui@gmail.com`)
   - `SMTP_USER` / `EMAIL_FROM` — your Gmail address
   - `SMTP_PASS` — the 16-char App Password
4. Test: `npm run premarket`

## Gating

- **Scanner A:** emails every run (once per day)
- **Scanner B:** emails only on first run of day, a new hit, or an error

## Shared sender

`scripts/lib/send_email.py` — used by both scanners (Python imports it; the
Node scanner shells out to it). SMTP over STARTTLS (587) or SSL (465).
