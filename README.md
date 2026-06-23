# Humbled Trader × TradingView MCP

Implementation of the [Humbled Trader setup guide](https://www.humbledtrader.com/blog/connect-claude-to-tradingview-mcp/) for **Cursor** (or Claude Code). Turns TradingView Desktop into an AI-assisted trading workflow: premarket scanners, intraday strategy filters, Pine backtests, and Telegram alerts.

## Prerequisites

| Requirement | Notes |
|---|---|
| **TradingView Desktop** | Paid plan (Essential+). Browser version does **not** work. |
| **Node.js 18+** | For [tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp) |
| **Cursor or Claude Code** | With MCP support |
| **Telegram bot** (optional) | For phone alerts (Step 11) |

## Quick start

### 1. Clone TradingView MCP (if not installed)

```bash
git clone https://github.com/tradesdontlie/tradingview-mcp.git ~/tradingview-mcp
cd ~/tradingview-mcp && npm install
```

### 2. Configure this project

```bash
cd ~/humbled-trader
cp .env.example .env
# Edit .env — add Telegram token/chat ID if you want alerts
```

MCP is preconfigured in `.cursor/mcp.json`. For global Cursor config, merge the `tradingview` block into `~/.cursor/mcp.json`.

### 3. Launch TradingView with debug port

```bash
npm run tv:launch
npm run tv:status   # expect cdp_connected: true, api_available: true
```

Or manually:

```bash
open -a TradingView --args --remote-debugging-port=9222
```

**Important:** Keep a real chart tab open (not the “New Tab” welcome screen).

### 4. Restart Cursor

MCP servers load on startup. Then ask the agent:

> Use tv_health_check to confirm TradingView is connected.

### 5. Run scanners

```bash
npm run premarket          # Scanner A — premarket gappers
npm run tjl                # Scanner B — Trend Join Long filter (needs TV running)
npm run install-schedule   # macOS launchd automation (Steps 6 & 8)
```

## What’s included

| Step (blog) | This repo |
|---|---|
| Install MCP | `SETUP.md`, `.cursor/mcp.json`, `scripts/launch_tradingview.sh` |
| Basic chart prompts | `prompts/02-basic-prompts.md` |
| Scanner A — premarket gappers | `scripts/premarket_gappers.py` |
| Automate Scanner A | `launchd/`, `scripts/catchup_premarket.sh` |
| Scanner B — TJL strategy | `scripts/tjl_strategy_scanner.mjs` |
| Automate Scanner B | `launchd/com.humbledtrader.tjl.plist.template` |
| Pine backtest | `pine/trend_join_breakout_v4_no_regime.pine`, `prompts/09-backtest.md` |
| Regime filter test | `prompts/10-regime-filter.md` |
| Telegram alerts | Built into both scanners via `.env` |

## Output files

- `premarket_gappers_YYYY-MM-DD.json`
- `tjl_watchlist_YYYYMMDD_HHMMET.json`

Both are gitignored. State for notification gating lives in `.state/`.

## Cursor vs Claude Code

The blog targets **Claude Code** (`~/.claude/.mcp.json`). This project uses **Cursor** (`~/.cursor/mcp.json` or project `.cursor/mcp.json`). The scanners run standalone via `npm run`; chart/Pine steps use MCP prompts in `prompts/`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `cdp_connected: false` | Quit TradingView fully, relaunch with `--remote-debugging-port=9222` |
| Port 9222 in use | Change `CDP_PORT` in `.env` and relaunch with new port |
| Scanner B fails | TradingView must be open with an active chart during market hours (10:00–15:30 ET) |
| Yahoo parse empty | Yahoo HTML changed — update `parse_yahoo_gainers()` in the Python script |

## Disclaimer

Unofficial integration using TradingView Desktop internals. Not financial advice. Paper-trade first.

## Credits

- Workflow: [Humbled Trader](https://www.humbledtrader.com/blog/connect-claude-to-tradingview-mcp/)
- MCP bridge: [@Tradesdontlie / tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp)
