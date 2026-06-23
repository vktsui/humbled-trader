Test whether adding an SPY/QQQ regime filter improves the strategy. Modify the SAME "Demo TJL Strategy" slot:

REGIME FILTER:
- At first 5-min bar at or after 10:00am ET, latch regime_ok:
  (SPY close > SPY prev daily close) AND (QQQ close > QQQ prev daily close)
- Add regime_ok == true to can_enter
- Red background tint on regime-fail days

Compare metrics in a table: Without regime vs With regime.
