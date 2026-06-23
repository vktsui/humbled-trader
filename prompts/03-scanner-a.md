Build me a premarket gappers scanner as a single shell script in this directory.

DATA SOURCE: WebFetch https://finance.yahoo.com/markets/stocks/gainers/
Parse out ticker, price, gap %, volume for each row.

FILTERS:
- premarket_volume > 50000
- Keep top 10 by gap_pct descending (cap at 10 for runtime)

NEWS CATALYST: For each of the top 10, WebFetch https://www.benzinga.com/quote/{TICKER} with this exact prompt: "What recent news or catalyst is driving {TICKER} stock today? Return a one-sentence summary, then up to 2 recent headlines verbatim. Just the data — no commentary."

IMPORTANT: Do NOT use https://finance.yahoo.com/quote/{TICKER}/news/ — that endpoint returns HTTP 503 reliably. Benzinga is the working source.

OUTPUT: Save to ./premarket_gappers_YYYY-MM-DD.json

After saving, print a one-line summary.

Note: This repo already includes `scripts/premarket_gappers.py` — run `npm run premarket` or extend that script.
