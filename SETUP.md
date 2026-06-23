# Setup Guide (from Humbled Trader blog)

Full walkthrough: https://www.humbledtrader.com/blog/connect-claude-to-tradingview-mcp/

This document maps each blog step to files/commands in this repo.

---

## Step 1 — AI agent (Cursor / Claude Code)

**Blog:** Install Claude Code via `curl -fsSL https://claude.ai/install.sh | bash`

**This repo:** Use **Cursor** with Agent mode. Paid plan recommended for automated Scanner B (runs up to 9×/day).

---

## Step 2 — TradingView Desktop

1. Subscribe to a paid TradingView plan (Essential minimum).
2. Download **Desktop** app from your TradingView account.
3. Sign in and pin any chart (e.g. SPY daily).

---

## Step 3 — Install TradingView MCP

```bash
git clone https://github.com/tradesdontlie/tradingview-mcp.git ~/tradingview-mcp
cd ~/tradingview-mcp && npm install
```

**Cursor MCP config** (project-level, already in `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "tradingview": {
      "command": "node",
      "args": ["/path/to/tradingview-mcp/versions/v1/src/server.js"]
    }
  }
}
```

**Launch TradingView:**

```bash
./scripts/launch_tradingview.sh launch
./scripts/launch_tradingview.sh status
```

Restart Cursor, then verify with agent prompt in `prompts/01-verify-connection.md`.

---

## Step 4 — Basic prompts

See `prompts/02-basic-prompts.md` — paste into Cursor chat one at a time.

---

## Step 5 — Scanner A (premarket gappers)

```bash
npm run premarket
```

Or use the full agent prompt in `prompts/03-scanner-a.md`.

---

## Step 6 — Automate Scanner A

```bash
npm run install-schedule
launchctl list | grep -i premarket
```

Schedules 8:30am ET weekdays + catch-up on login if the laptop was asleep.

---

## Step 7 — Scanner B (TJL strategy)

Requires TradingView running 10:00–15:30 ET with CDP port open.

```bash
npm run tjl
```

Full agent prompt: `prompts/07-scanner-b.md`

---

## Step 8 — Automate Scanner B

Included in `npm run install-schedule` — fires every 30 minutes 10:00am–2:00pm ET weekdays. Telegram only on first run of day or new hits.

---

## Step 9 — Pine backtest

1. Open Pine slot named **"Demo TJL Strategy"** in TradingView.
2. Use agent prompt `prompts/09-backtest.md` with code from `pine/trend_join_breakout_v4_no_regime.pine`.

---

## Step 10 — Regime filter A/B test

Agent prompt: `prompts/10-regime-filter.md`

---

## Step 11 — Email alerts

1. Create a Gmail **App Password**: https://myaccount.google.com/apppasswords (requires 2FA)
2. Copy `.env.example` → `.env` and set `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM` (recipient `EMAIL_TO` defaults to `vktsui@gmail.com`)
3. Run `npm run premarket` to test delivery

Full prompt: `prompts/11-email.md`. Shared sender: `scripts/lib/send_email.py`.

---

## Step 12 — Paper trading (optional)

Connect broker paper account in TradingView separately. MCP reads charts; execution requires explicit consent via trading tools.
