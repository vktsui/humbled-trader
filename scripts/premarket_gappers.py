#!/usr/bin/env python3
"""
Premarket Gappers Scanner (Scanner A) — Humbled Trader workflow.

Fetches Yahoo premarket gainers, filters by volume, pulls Benzinga catalysts,
saves JSON, and optionally notifies Telegram.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from send_email import send_email  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MIN_PREMARKET_VOLUME = 50_000
TOP_N = 10
USER_AGENT = "Mozilla/5.0 (compatible; humbled-trader/1.0)"


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_yahoo_gainers(html: str) -> list[dict]:
    """Parse gainers from Yahoo markets page (table rows)."""
    rows: list[dict] = []
    # Match table row chunks with ticker links
    for block in re.findall(r"<tr[^>]*>.*?</tr>", html, flags=re.S | re.I):
        sym_m = re.search(r'href="/quote/([A-Z0-9.\-^]+)/"', block, re.I)
        if not sym_m:
            continue
        symbol = sym_m.group(1).upper()
        nums = re.findall(r'data-field="regularMarket(?:Price|ChangePercent|Volume)"[^>]*>([^<]+)<', block)
        if len(nums) < 2:
            nums = re.findall(r">([\d,]+\.?\d*)%?<", block)
        cells = re.findall(r">([^<]{1,40})<", block)
        price = None
        gap_pct = None
        volume = None
        for c in cells:
            c = c.strip().replace(",", "")
            if c.endswith("%") and gap_pct is None:
                try:
                    gap_pct = float(c.rstrip("%"))
                except ValueError:
                    pass
            elif re.fullmatch(r"\d+\.?\d*", c) and price is None and "." in c:
                try:
                    price = float(c)
                except ValueError:
                    pass
        vol_m = re.search(r"([\d,]+)\s*(?:Vol|Volume)?", block, re.I)
        if vol_m:
            try:
                volume = int(vol_m.group(1).replace(",", ""))
            except ValueError:
                pass
        if price is None or gap_pct is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "price": price,
                "gap_pct": gap_pct,
                "premarket_volume": volume or 0,
            }
        )
    return rows


def fetch_benzinga_catalyst(symbol: str) -> tuple[str | None, list[str]]:
    url = f"https://www.benzinga.com/quote/{symbol}"
    try:
        html = fetch(url, timeout=20)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  catalyst fetch failed for {symbol}: {e}", file=sys.stderr)
        return None, []

    headlines: list[str] = []
    for m in re.finditer(r'<h[23][^>]*>([^<]{10,200})</h[23]>', html, re.I):
        t = unescape(m.group(1)).strip()
        if t and t not in headlines:
            headlines.append(t)
        if len(headlines) >= 2:
            break

    catalyst = headlines[0] if headlines else None
    return catalyst, headlines[:2]


def main() -> int:
    load_env()
    today = date.today().isoformat()
    out_path = ROOT / f"premarket_gappers_{today}.json"

    if out_path.exists():
        print(f"Already scanned today: {out_path}")
        return 0

    print("Fetching Yahoo premarket gainers...")
    html = fetch("https://finance.yahoo.com/markets/stocks/gainers/")
    raw = parse_yahoo_gainers(html)
    if not raw:
        print("No gainers parsed — Yahoo HTML layout may have changed.", file=sys.stderr)
        return 1

    filtered = [r for r in raw if r["premarket_volume"] > MIN_PREMARKET_VOLUME]
    filtered.sort(key=lambda x: x["gap_pct"], reverse=True)
    top = filtered[:TOP_N]

    results = []
    for i, row in enumerate(top, start=1):
        print(f"  catalyst: {row['symbol']}...")
        catalyst, headlines = fetch_benzinga_catalyst(row["symbol"])
        results.append(
            {
                "rank": i,
                "symbol": row["symbol"],
                "price": row["price"],
                "gap_pct": row["gap_pct"],
                "premarket_volume": row["premarket_volume"],
                "catalyst": catalyst,
                "headlines": headlines,
            }
        )

    payload = {
        "scanned_at": datetime.now().astimezone().isoformat(),
        "gappers": results,
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n")

    top3 = results[:3]
    parts = [
        f"{g['symbol']} ({g['gap_pct']:+.1f}%) — {g['catalyst'] or 'no catalyst'}"
        for g in top3
    ]
    summary = (
        f"Premarket Gappers: {len(results)} names. Top: " + ", ".join(parts)
    )
    print(summary)

    if results:
        lines = [f"Premarket Gappers — {today}", ""]
        for g in results:
            cat = f" — {g['catalyst']}" if g["catalyst"] else ""
            lines.append(
                f"  {g['symbol']}  ${g['price']:.2f}  +{g['gap_pct']:.1f}%{cat}"
            )
        send_email(f"Premarket Gappers — {today}", "\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
