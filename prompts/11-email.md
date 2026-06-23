# Step 11 — Email alerts

Both scanners email results to **vktsui@gmail.com** after saving their JSON.

The sender (`scripts/lib/send_email.py`) auto-selects a backend from `.env`,
in priority order: **Resend → SendGrid → SMTP**.

## Recommended: Resend (no SMTP password)

1. Sign up at https://resend.com with **vktsui@gmail.com**
2. Create an API key (Dashboard → API Keys)
3. In `.env` set:
   ```
   RESEND_API_KEY=re_xxxxxxxx
   EMAIL_FROM=onboarding@resend.dev
   EMAIL_TO=vktsui@gmail.com
   ```
   On the free tier with no verified domain, Resend delivers from
   `onboarding@resend.dev` **to your signup email** — perfect here.
   To send from your own address to anyone, add a verified domain in Resend.
4. Test: `npm run premarket`

## Alternative: SendGrid

1. Sign up, verify a **Single Sender** (your from-address), create an API key.
2. In `.env`: `SENDGRID_API_KEY=SG.xxx` and `EMAIL_FROM=<verified sender>`.

## Alternative: Gmail SMTP

Needs a Gmail **App Password** (https://myaccount.google.com/apppasswords).
Set `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM` in `.env`.

## Gating

- **Scanner A:** emails every run (once per day)
- **Scanner B:** emails only on first run of day, a new hit, or an error
