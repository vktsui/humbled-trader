Build me a Trend Join Long strategy scanner that filters tickers down to which ones meet my day-trading entry criteria right now.

TEST UNIVERSE: 3 tickers — AMD, NVDA, MU.

PREREQ: TradingView Desktop must be running with CDP port 9222 enabled. First call tv_health_check. If cdp_connected=false OR api_available=false, stop and tell me to launch TV with: `open -a TradingView --args --remote-debugging-port=9222`.

TIME GATE: Only proceed if current time is between 10:00am and 3:30pm New York time.

FOR EACH TICKER (sequential):
1. chart_set_symbol
2. Daily OHLCV (210 bars) → prev_daily_high, prev_daily_close, sma200
3. quote_get → curr_px
4. 1-min OHLCV (400 bars) → pmh, today_hod
5. PASS if (curr_px > prev_daily_high AND prev_daily_close > sma200) AND (curr_px > pmh AND curr_px > today_hod)

OUTPUT: Save to ./tjl_watchlist_YYYY-MM-DD_HHMMET.json

Note: This repo includes `scripts/tjl_strategy_scanner.mjs` — run `npm run tjl`.
