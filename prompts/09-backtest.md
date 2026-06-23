Build a Trend Join Long strategy backtest in TradingView end-to-end:

1. Call tv_health_check. Confirm cdp_connected=true and api_available=true.
2. chart_set_symbol("AMD"), chart_set_timeframe("5"), enable Extended Hours.
3. Open Pine slot "Demo TJL Strategy" with pine_open — DO NOT use pine_new.
4. Inject code from `pine/trend_join_breakout_v4_no_regime.pine` using pine_set_source, then pine_smart_compile.
5. Apply to chart via ui_find_element + ui_mouse_click on Add to chart.
6. capture_screenshot region="strategy_tester" and report win rate, total trades, P&L, profit factor.
